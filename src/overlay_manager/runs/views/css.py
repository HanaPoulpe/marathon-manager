from django.views import generic


class CSSView(generic.TemplateView):
    template_name = "main.css"
    content_type = "text/css"
