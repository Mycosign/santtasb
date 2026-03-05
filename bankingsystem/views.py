from django.views.generic import TemplateView

class StaticHTMLView(TemplateView):
    template_name = None  # Initialize template_name as None

    def get_template_names(self):
        page_name = self.kwargs.get('page_name')
        if page_name:
            self.template_name = f'static_html/{page_name}.html'
        return super().get_template_names()