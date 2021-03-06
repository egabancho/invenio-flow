# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow python API."""

import logging
from functools import wraps
from itertools import repeat

from celery import Task as CeleryTask
from celery import chain as celery_chain
from celery import current_app as celery_app
from celery import group as celery_group
from celery.task.control import revoke
from invenio_db import db

from .models import Flow as FlowModel
from .models import Status
from .models import Task as TaskModel
from .models import as_task
from .utils import uuid

logger = logging.getLogger('invenio-flow')


def align_arguments(f):
    """Align tasks and tasks arguments decorator."""
    @wraps(f)
    def inner(self, task, task_kwargs=None):
        if isinstance(task, list) and not isinstance(task_kwargs, list):
            task_kwargs = list(repeat(task_kwargs, len(task)))
        elif not isinstance(task, list) and isinstance(task_kwargs, list):
            task = list(repeat(task, len(task_kwargs)))
        elif not isinstance(task, list) and not isinstance(task_kwargs, list):
            task = [
                task,
            ]
            task_kwargs = [
                task_kwargs,
            ]

        task_kwargs.extend([None] * (len(task) - len(task_kwargs)))

        return f(self, task, task_kwargs)

    return inner


class Flow(object):
    """Flow class."""

    def __init__(self, model=None):
        """Initialize the flow object."""
        self.model = model
        self._tasks = []
        self._canvas = []

    @property
    def id(self):
        """Get flow identifier."""
        return self.model.id if self.model else None

    @property
    def name(self):
        """Get flow name."""
        return self.model.name if self.model else None

    @property
    def payload(self):
        """Get flow payload."""
        return self.model.payload if self.model else None

    @property
    def previous_id(self):
        """Get the previous run of the flow."""
        return self.model.previous_id if self.model else None

    @payload.setter
    def payload(self, value):
        """Update payload."""
        if self.model:
            self.model.payload = value
            db.session.merge(self.model)

    @property
    def created(self):
        """Get creation timestamp."""
        return self.model.created if self.model else None

    @property
    def updated(self):
        """Get last updated timestamp."""
        return self.model.updated if self.model else None

    @property
    def status(self):
        """Get flow status."""
        if self.model is None:
            return None

        return {
            **self.model.to_dict(),
            'tasks': [t.to_dict() for t in self.model.tasks],
        }

    @classmethod
    def get_flow(cls, id_):
        """Retrieve a Flow from the database by Id."""
        obj = FlowModel.get(id_)
        return cls(obj)

    @classmethod
    def create(cls, name, payload=None, id_=None, previous_id=None):
        """Create a new flow instance and store it in the database.."""
        with db.session.begin_nested():
            obj = FlowModel(
                name=name,
                id=id_ or uuid(),
                payload=payload or dict(),
                previous_id=previous_id,
            )
            db.session.add(obj)
        logger.info('Created new Flow %s', obj)
        return cls(model=obj)

    @align_arguments
    def chain(self, task, task_kwargs=None):
        """Appends new tasks to the canvas to be run in series."""
        self._tasks.extend(zip(task, task_kwargs))
        return self

    @align_arguments
    def group(self, task, task_kwargs=None):
        """Appends new group of tasks to the canvas to run in parallel."""
        self._tasks.append(list(zip(task, task_kwargs)))
        return self

    def _new_task(self, task, kwargs, previous):
        """Create a new task associate with the flow."""
        task_id = uuid()
        kwargs = kwargs if kwargs else {}
        signature = task.signature(
            task_id=task_id,
            kwargs={
                'flow_id': str(self.id),
                'task_id': task_id,
                **kwargs,
                **self.payload,  # TODO: Do we need to move this to a key?
            },
            immutable=True,  # TODO, ad this as an option/parameter?
        )

        _ = TaskModel.create(
            id_=task_id,
            flow_id=self.id,
            name=task.name,
            previous=previous,
            payload=kwargs,
        )

        return signature

    def build(self):
        """."""
        raise NotImplementedError()

    def assemble(self, build_func):
        """Build the canvas out of the task list."""
        if self.model is None:
            raise RuntimeError('No database flow object found.')
        if self.model.tasks:
            raise RuntimeError(
                'This flow instance was already assembled, use create'
                'to create a new instance and restart the flow.'
            )

        build_func(self)

        previous = []
        for task in self._tasks:
            if isinstance(task, tuple):
                signature = self._new_task(*task, previous)
                self._canvas.append(signature)
                previous = [signature.id]
            elif isinstance(task, list):
                sub_canvas = [self._new_task(*t, previous) for t in task]
                previous = [t.id for t in sub_canvas]
                self._canvas.append(celery_group(sub_canvas, task_id=uuid()))
            else:
                raise RuntimeError(
                    'Error while parsing the task list %s', self._tasks
                )

        self._canvas = celery_chain(*self._canvas, task_id=self.id)

        return self

    def start(self):
        """Start the flow asynchronously."""
        if not self._canvas:
            self.assemble()
        return self._canvas.apply_async()

    def stop(self):
        """Stop the flow."""
        revoke(
            [
                str(task.id)
                for task in self.model.tasks
                if task.status == Status.PENDING
            ],
            terminate=True,
            signal='SIGKILL',  # TODO: do we need this?
        )

    def get_task_status(self, task_id):
        """Get singular task status."""
        try:
            task = as_task(task_id)
        except Exception:
            raise KeyError('Task ID %s not in flow %s', task_id, self.id)

        return {'status': str(task.status), 'message': task.message}

    def stop_task(self, task_id):
        """Stop singular task."""
        try:
            task = as_task(task_id)
        except Exception:
            raise KeyError('Task ID %s not in flow %s', task_id, self.id)

        if task.status == Status.PENDING:
            revoke(str(task.id), terminate=True, signal='SIGKILL')

    def restart_task(self, task_id):
        """Restart singular task."""
        try:
            task = as_task(task_id)
        except Exception:
            raise KeyError('Task ID %s not in flow %s', task_id, self.id)

        self.stop_task(task)

        task.status = Status.PENDING
        db.session.add(task)

        signature = (
            celery_app.tasks.get(task.name)
            .signature(
                task_id=str(task.id),
                kwargs={
                    'flow_id': str(self.id),
                    'task_id': str(task.id),
                    **task.payload,
                    **self.payload,  # TODO: Do we need to move this to a key?
                },
                immutable=True,  # TODO, ad this as an option/parameter?
            )
            .apply_async()
        )


class Task(CeleryTask):
    """The task class which is used as the minimal unit of work.

    This class is a wrapper around ``celery.Task``
    """

    def commit_status(self, task_id, state=Status.PENDING, message=''):
        """Commit task status to the database."""
        with celery_app.flask_app.app_context(), db.session.begin_nested():
            task = TaskModel.get(task_id)
            task.status = state
            task.message = message
            db.session.merge(task)
        db.session.commit()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Update task status on database."""
        task_id = kwargs.get('task_id', task_id)
        self.commit_status(task_id, Status.FAILURE, str(einfo))
        super(Task, self).on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Update tasks status on database."""
        task_id = kwargs.get('task_id', task_id)
        self.commit_status(
            task_id,
            Status.SUCCESS,
            'Task finished with return value: {}'.format(retval),
        )
        super(Task, self).on_success(retval, task_id, args, kwargs)
