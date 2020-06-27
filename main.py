import attr
import re
import tgalice


from tgalice.dialog import Response


@attr.s
class SessionState:
    current_lesson: int = attr.ib(default=None)
    current_section: int = attr.ib(default=None)


# todo: move it to a separate yaml file
sounds = {
    1: {
        'intro': '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/6d22ecca-a0b1-45c7-ba46-4b6ddc1e9164.opus">',
        'parts': [
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/0267feb2-5190-4292-b16c-cfa406e7ca8b.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/e27a7a57-7a49-4ac4-8afb-fa5db4fdf564.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/42b50d30-c9b0-4d51-85b4-7b5cda7b0177.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/a5e21ccb-3357-4311-97db-1f28ee1692e3.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/f83171d5-e364-4ff0-85b5-065ee853f5da.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/83dcc783-6399-48bd-a449-0890ecf2c180.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/303cfbd5-e37b-430e-9698-41792e1a0010.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/dd2f2cf6-d9da-4851-babe-a7a59c114494.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/4cdc757d-e12f-43be-9734-c33f910ae4ca.opus">',
            '<speaker audio="dialogs-upload/6acdf357-0325-4346-b5ab-4b83db0c2ca4/444cf2d2-93ff-48af-a342-82d8c30f895a.opus">',
        ]
    }
}


E_CONTENT_TYPE = {
    'lesson': ['урок', 'занятие'],
    'section': ['часть', 'секция'],
}
E_CONTENT_TYPE_INVERSE = {expr: k for k, v in E_CONTENT_TYPE.items() for expr in v}


def parse_request(text):
    result = {}
    if not text:
        return {}

    content_types = '|'.join(expr for v in E_CONTENT_TYPE.values() for expr in v)
    match = re.match(
        '(включи|запусти)?\\s*'
        f'(?P<content_type>{content_types})?\\s*'
        '(?P<content_id>\\d+)',
        text
    )
    if match:
        slots = match.groupdict()
        if 'content_type' in slots:
            slots['content_type'] = E_CONTENT_TYPE_INVERSE.get(slots['content_type'], slots['content_type'])
        result['choose'] = {'slots': {k: {'value': v} for k, v in slots.items()}}

    if re.match('дальше|вперед|следующий', text):
        result['next'] = {'slots': {}}

    return result


def nlg_lesson(lesson_id):
    lesson = sounds[lesson_id]
    return (
        f'<text>Запускаю урок {lesson_id}. </text>'
        f'{lesson["intro"]}'
        f'Чтобы продолжить, скажите "дальше" или номер секции.'
    )


def nlg_section(lesson_id, section_id):
    lesson = sounds[lesson_id]
    return (
        f'<text>Урок {lesson_id} часть {section_id}. </text>'
        f'{lesson["parts"][section_id-1]}'
        f'<text>Чтобы продолжить, скажите "дальше" или номер секции. </text>'
    )


def process_lesson(content_id: int, response: Response, ss: SessionState):
    if content_id not in sounds.keys():
        response.set_rich_text(
            f'Такого урока у меня нет. Назовите номер от {min(sounds.keys())} до {max(sounds.keys())}.'
        )
        ss.current_lesson = None
        ss.current_section = None
        response.suggests = [str(i) for i in sounds.keys()]
    else:
        ss.current_lesson = content_id
        ss.current_section = 0
        response.set_rich_text(nlg_lesson(content_id))


def process_section(content_id: int, response: Response, ss: SessionState):
    if ss.current_lesson is None:
        response.set_rich_text('Сначала выберите урок.')
        response.suggests = [str(i) for i in sounds.keys()]
    else:
        lesson = sounds[ss.current_lesson]
        n = len(lesson['parts'])
        if content_id > n or content_id <= 0:
            response.set_rich_text(f'В уроке {ss.current_lesson} только {n} частей.')
        else:
            ss.current_section = content_id
            response.set_rich_text(nlg_section(ss.current_lesson, content_id))


class KTDM(tgalice.dialog_manager.BaseDialogManager):
    def respond(self, ctx: tgalice.dialog.Context):
        uo = ctx.user_object or {}
        ss = SessionState(**uo.get('session', {}))
        forms = parse_request(text=ctx.message_text)
        if ctx.yandex and ctx.yandex.request.nlu.intents:
            forms.update({k: v.to_dict() for k, v in ctx.yandex.request.nlu.intents.items()})
        response = Response(
            'привет',
            user_object={'session': ss.__dict__}
        )

        if not ctx.message_text or ctx.session_is_new():
            response.set_rich_text(
                'Навык «Кинестетик-планшет» включен. Назовите номер урока.'
            )
            response.suggests = [str(i) for i in sounds.keys()]
        elif 'choose' in forms:
            form = forms['choose']['slots']
            content_id = int(form['content_id']['value'])
            content_type = form.get('content_type', {}).get('value')
            if content_type == 'lesson':
                process_lesson(content_id=content_id, response=response, ss=ss)
            elif content_type == 'section':
                process_section(content_id=content_id, response=response, ss=ss)
            else:
                if ss.current_lesson is None:
                    process_lesson(content_id=content_id, response=response, ss=ss)
                else:
                    process_section(content_id=content_id, response=response, ss=ss)
        elif 'next' in forms:
            if ss.current_section is not None:
                process_section(content_id=ss.current_section + 1, ss=ss, response=response)
            elif ss.current_lesson is not None:
                process_lesson(content_id=ss.current_lesson, response=response, ss=ss)
            else:
                process_lesson(content_id=min(sounds.keys()), response=response, ss=ss)
        elif tgalice.basic_nlu.like_exit(ctx.message_text):
            response.set_rich_text('Всего хорошего, до встречи в навыке "Кинестетик Планшет!"')
            response.commands.append(tgalice.COMMANDS.EXIT)
        elif tgalice.basic_nlu.like_help(ctx.message_text):
            response.set_rich_text(
                'Вы в навыке "Кинестетик-планшет". '
                'Кинестетик-планшет - это планшет для слепых и слабовидящих детей.'
                'В этом навыке реализованы звуковые уроки для его пользователей. '
                'Назовите номер урока (сейчас пока есть только один). '
                'Для выхода из навыка скажите "Хватит".'
            )
        else:
            response.set_rich_text('Вы в навыке "Кинестетик-планшет". '
                                   'Назовите номер урока или скажите "хватит"')

        response.user_object['session'] = ss.__dict__
        if ss.current_lesson and ss.current_section and not response.suggests:
            response.suggests.append('дальше')
            if ss.current_section > 1:
                response.suggests.append(str(ss.current_section - 1))
            response.suggests.append(str(ss.current_section))
            if ss.current_section < len(sounds[ss.current_lesson]['parts']):
                response.suggests.append(str(ss.current_section + 1))
        return response


manager = KTDM()

db = tgalice.message_logging.get_mongo_or_mock()

connector = tgalice.dialog_connector.DialogConnector(
    dialog_manager=manager,
    storage=tgalice.storage.session_storage.BaseStorage(),
    log_storage=tgalice.storage.message_logging.MongoMessageLogger(
        collection=db.get_collection('logs'), detect_pings=True,
    ),
    alice_native_state=True,
)

alice_handler = connector.serverless_alice_handler


if __name__ == '__main__':
    server = tgalice.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
