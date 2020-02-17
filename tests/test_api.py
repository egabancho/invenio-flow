# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Python basic API tests."""

from __future__ import absolute_import, print_function

from invenio_flow import Flow, task

from invenio_flow.models import Task


def test_basic_flow_api_usage(db):
    """Test basic flow creation."""

    @task
    def t1(common, **kwargs):
        """Task with an important mission."""
        # if common == 'common-arg':
        #     raise Exception()
        print('Run t1', common, kwargs)

    @task
    def t2(p, **kwargs):
        """Task with an even more important mission."""
        if p == 't2_1':
            # This one doesn't actually run anything, we just return
            return 'No need to run for {}'.format(p)

        # Do important stuff when required
        print('Run t2', p, kwargs)

    @task
    def t3(**kwargs):
        """Task with a secret mission."""
        print('Run t3', kwargs)

    @task(bind=True, max_retries=None)
    def t4(self, times, **kwargs):
        """Run this one n times."""
        print('Run t4: ', times, kwargs)
        if times > 0:
            self.commit_status(
                kwargs['task_id'], message='Running for {}'.format(times)
            )
            # Testing message updates
            t = Task.get(kwargs['task_id'])
            assert t.status.value == 'PENDING'
            assert t.message == 'Running for {}'.format(times)
            f = Flow.get_flow(kwargs['flow_id'])
            assert f.status['status'] == 'PENDING'

            # Reschedule the task to mimic breaking long standing tasks
            times = times - 1
            self.retry(args=(times,), kwargs=kwargs)

    flow = Flow.create('test', payload=dict(common='common-arg'))
    assert flow.status['status'] == 'PENDING'

    # build the workflow
    def build(flow):
        flow.chain(t1)
        flow.group(t2, [{'p': 't2_1'}, {'p': 't2_2'}])
        flow.chain(t3, {'p': 't3'})
        flow.chain(t4, {'times': 10})

    flow.assemble(build)

    # Save tasks and flow before running
    db.session.commit()

    assert flow.status['status'] == 'PENDING'

    flow.start()

    flow = Flow.get_flow(flow.id)
    assert flow.status['status'] == 'SUCCESS'

    task_status = flow.status['tasks'][0]
    assert task_status['status'] == 'SUCCESS'
    flow_task_status = flow.get_task_status(task_status['id'])
    assert flow_task_status['status'] == 'SUCCESS'

    # Create a new instance of the same flow (restart)
    old_flow_id = flow.id
    flow = flow.__class__.create(
        flow.name, payload={'common': 'test 2'}, previous_id=old_flow_id
    )
    assert flow.status['status'] == 'PENDING'
    flow.assemble(build)

    # Save tasks and flow before running
    db.session.commit()

    assert flow.status['status'] == 'PENDING'

    flow.start()

    assert flow.id != old_flow_id

    flow = Flow.get_flow(flow.id)
    assert flow.previous_id == old_flow_id

    # Restart task
    flow.restart_task(task_status['id'])
    flow_task_status = flow.get_task_status(task_status['id'])
    assert flow_task_status['status'] == 'SUCCESS'
