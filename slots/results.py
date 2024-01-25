from pylon.core.tools import web, log

from tools import auth
from tools import theme


class Slot:
    slot = lambda name: web.slot(f'security_app_results_{name}')

    @slot('content')
    @auth.decorators.check_slot(
        {"permissions": ["security.app.results"]},
        access_denied_reply=theme.access_denied_part
    )
    def content(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        log.info('payload request args: [%s]', payload.request.args)
        result_id = payload.request.args.get('result_id')
        if result_id:
            test_data = self.results_or_404(result_id)
            with context.app.app_context():
                return self.descriptor.render_template(
                    'results/content.html',
                    test_data=test_data
                )
        return theme.empty_content

    @slot('scripts')
    @auth.decorators.check_slot(
        {"permissions": ["security.app.results"]},
        access_denied_reply=theme.access_denied_part
    )
    def scripts(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        use_sio_logs = self.descriptor.config.get("use_sio_logs", False)
        result_id = payload.request.args.get('result_id')
        if result_id:
            test_data = self.results_or_404(result_id)
            with context.app.app_context():
                return self.descriptor.render_template(
                    'results/scripts.html',
                    test_data=test_data,
                    use_sio_logs=use_sio_logs
                )
        return ''

    @slot('styles')
    @auth.decorators.check_slot(
        {"permissions": ["security.app.results"]},
        access_denied_reply=theme.access_denied_part
    )
    def styles(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'results/styles.html',
            )
