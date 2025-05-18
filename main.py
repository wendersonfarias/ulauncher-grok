import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
import requests

logger = logging.getLogger(__name__)
EXTENSION_ICON = 'images/icon.png'

def wrap_text(text, max_w):
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        if len(current_line + ' ' + word) <= max_w:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())
    return '\n'.join(lines)

class GroqExtension(Extension):
    def __init__(self):
        super(GroqExtension, self).__init__()
        logger.info('Groq extension started')
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        logger.info('Processing user preferences')
        try:
            api_key = extension.preferences['groq_api_key']
            model = extension.preferences['model']
            line_wrap = int(extension.preferences['line_wrap'])
        except Exception as err:
            logger.error('Failed to parse preferences: %s', str(err))
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=EXTENSION_ICON,
                    name='Failed to parse preferences: ' + str(err),
                    on_enter=CopyToClipboardAction(str(err))
                )
            ])

        if not api_key:
            err_msg = "Groq API key not configured!"
            logger.error(err_msg)
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=EXTENSION_ICON,
                    name=err_msg,
                    on_enter=CopyToClipboardAction(err_msg)
                )
            ])

        search_term = event.get_argument()
        logger.info('The search term is: %s', search_term)

        if not search_term:
            logger.info('Displaying blank prompt')
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=EXTENSION_ICON,
                    name='Type in a prompt...',
                    on_enter=DoNothingAction()
                )
            ])

        endpoint = "https://api.groq.com/openai/v1/chat/completions "
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        body = {
            "model": model,
            "messages": [
                {"role": "user", "content": search_term}
            ]
        }

        try:
            logger.info('Sending request to Groq API')
            response = requests.post(endpoint, headers=headers, json=body, timeout=10)
            response.raise_for_status()
        except Exception as err:
            logger.error('Request failed: %s', str(err))
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=EXTENSION_ICON,
                    name='Request failed: ' + str(err),
                    on_enter=CopyToClipboardAction(str(err))
                )
            ])

        try:
            data = response.json()
            message = data['choices'][0]['message']['content']
            message_wrapped = wrap_text(message, line_wrap)
        except Exception as err:
            logger.error('Failed to parse response: %s', str(err))
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=EXTENSION_ICON,
                    name='Failed to parse response: ' + str(err),
                    on_enter=CopyToClipboardAction(str(err))
                )
            ])

        items = [
            ExtensionResultItem(
                icon=EXTENSION_ICON,
                name='Assistant',
                description=message_wrapped,
                on_enter=CopyToClipboardAction(message)
            )
        ]

        return RenderResultListAction(items)

if __name__ == '__main__':
    GroqExtension().run()
