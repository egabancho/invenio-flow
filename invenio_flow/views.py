# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow REST API."""

from functools import wraps, partial

from flask import Blueprint, abort, current_app, jsonify, request
from invenio_rest import ContentNegotiatedMethodView
from sqlalchemy.exc import SQLAlchemyError

from .api import Flow
from .permissions import need_permission
from .proxies import current_flow
from .utils import uuid

blueprint = Blueprint('invenio_flow', __name__, url_prefix='/flows')


def pass_payload(f):
    """Extract json payload from request."""

    @wraps(f)
    def inner(self, *args, **kwargs):
        payload = request.get_json() or None
        return f(*args, payload=payload, **kwargs)

    return inner


def pass_flow(f):
    """Retrieve the Flow instance from the database."""

    @wraps(f)
    def inner(self, flow_name, flow_id, *args, **kwargs):
        try:
            flow_cls = current_flow.get_flow_class(flow_name)
            flow = flow_cls.get_flow(flow_id)
            return f(flow=flow, *args, **kwargs)
        except (KeyError, SQLAlchemyError):
            abort(404)

    return inner


class NewFlowResource(ContentNegotiatedMethodView):
    """Flow Resource."""

    @pass_payload
    @need_permission(
        lambda self, flow_name, payload, **kwargs: (flow_name, payload),
        'flow-create',
    )
    def post(self, flow_name, payload, **kwargs):
        """Create new flow instance with the payload."""
        try:
            flow_cls = current_flow.get_flow_class(flow_name)
        except KeyError:
            abort(404)
        flow = flow_cls.create(name=flow_name, payload=payload)
        db.session.commmit()

        response = jsonify(flow.id)
        response.status_code = 201
        return response


class FlowResource(ContentNegotiatedMethodView):
    """FLow Resource."""

    @pass_flow
    @need_permission(lambda self, flow, **kwargs: (flow,), 'flow-status')
    def get(self, flow, **kwargs):
        """Get flow status."""
        return jsonify(flow.status)

    @pass_flow
    @pass_payload
    @need_permission(
        lambda self, flow, payload, **kwargs: (flow, payload), 'flow-start'
    )
    def post(self, flow, payload, **kwargs):
        """Start flow with payload.

        If the payload is ``None`` the previous one used to create the flow
        will be used.
        """
        if payload:
            # Update payload with the new one
            flow.payload = payload

        build_func = current_flow.get_flow_build_func(flow.name)
        flow = flow.assemble(build_func)

        db.session.commit()

        flow.start()

        # FIXME: we can do better than this!
        db.session.refresh(flow.model)

        return jsonify(flow.status)

    @pass_flow
    @pass_payload
    @need_permission(
        lambda self, flow, payload, **kwargs: (flow, payload), 'flow-restart'
    )
    def put(self, flow, payload, **kwargs):
        """Restart the flow with payload."""
        flow.stop()

        # Create a new flow run and store the old one for reference
        flow = flow.__class__.create(
            flow.name, payload=payload or flow.payload, previous_id=flow.id
        )

        build_func = current_flow.get_flow_build_func(flow.name)
        flow = flow.assemble(build_func)

        db.session.commit()

        flow.start()

        # FIXME: we can do better than this!
        db.session.refresh(flow.model)

        response = jsonify(flow.id)
        response.status_code = 201
        return response

    @pass_flow
    @need_permission(lambda self, flow, **kwargs: (flow,), 'flow-stop')
    def delete(self, flow, **kwargs):
        """Stop a running flow."""
        flow.stop()
        return '', 202


need_task_permission = partial(
    need_permissions, lambda self, flow, task_id, **kwargs: (flow, task_id)
)


class TaskResource(ContentNegotiatedMethodView):
    """Task resource."""

    @pass_flow
    @need_task_permission('flow-task-status')
    def get(self, flow, task_id, **kwargs):
        """Get task status."""
        try:
            status = flow.get_task_status(task_id)
        except KeyError:
            abort(404)
        return jsonify(status)

    @pass_flow
    @need_task_permission('flow-task-restart')
    def put(self, flow, task_id, **kwargs):
        """Restart the task at hand."""
        try:
            flow.restart_task(task_id)
        except KeyError:
            abort(404)
        return '', 202

    @pass_flow
    @need_task_permission('flow-task-stop')
    def delete(self, flow, task_id, **kwargs):
        """Stop a running task."""
        try:
            flow.stop_task(task_id)
        except KeyError:
            abort(404)
        return '', 202


blueprint.add_url_rule(
    '/<string:flow_name>', view_func=NewFlowResource.as_view('new_flow_api')
)

blueprint.add_url_rule(
    '/<string:flow_name>/<uuid:flow_id>',
    view_func=FlowResource.as_view('flow_api'),
)

blueprint.add_url_rule(
    '/<string:flow_name>/<uuid:flow_id>/<uuid:task_id>',
    view_func=TaskResource.as_view('flow_task_api'),
)
