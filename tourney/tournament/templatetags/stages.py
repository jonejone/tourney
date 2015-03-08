from django.utils.translation import ugettext_lazy as _
from django import template

register = template.Library()

@register.tag('get_stage_requirement')
def get_stage(parser, token):
    try:
        cmd, stage_var, class_var = token.contents.split(None)
    except ValueError:
        raise template.TemplateSyntaxError('Requires stage, class')

    return StageRequirementNode(stage_var, class_var)


class StageRequirementNode(template.Node):
    def __init__(self, stage_var, class_var):
        self.stage_var = stage_var
        self.class_var = class_var

    def render(self, context):
        stage = context[self.stage_var]
        class_ = context[self.class_var]

        stage_class = stage.registrationstageclass_set.filter(
            player_class=class_).order_by('-id')[0]

        if stage_class.rating_required > 0:
            return stage_class.rating_required
        else:
            return _('All')

