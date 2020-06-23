import tgalice
import yaml


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

# todo: download the yaml from github instead
with open('menu.yaml', 'r', encoding='utf-8') as f:
    menu = yaml.safe_load(f)

for lesson_id, lesson in sounds.items():
    parts = lesson['parts']
    nexts = [
        {'intent': f'{i + 1}', 'label': f'L{lesson_id}P{i + 1}'}
        for i in range(len(parts))
    ]
    menu['states'][f'L{lesson_id}'] = {
        'q': [f'включи урок {lesson_id}', f'включи урок номер {lesson_id}'],
        'a': f'<text>Запускаю урок {lesson_id}.</text>'
             f'{lesson["intro"]}'
             f'Чтобы продолжить, скажите "дальше" или номер секции.',
        'next': nexts + [{'suggest': 'дальше', 'intent': 'FORWARD', 'label': f'L{lesson_id}P1'}],
    }
    for part_id, part in enumerate(parts):
        part_code = {
            'a': f'<text>Урок {lesson_id} часть {part_id+1}.</text>'
                 f'{part}'
                 f'Чтобы продолжить, скажите "дальше" или номер секции.',
            'next': nexts[:],
        }
        if part_id < len(parts) - 1:
            part_code['next'].append(
                {'suggest': 'дальше', 'intent': 'FORWARD', 'label': f'L{lesson_id}P{part_id+2}'}
            )
        menu['states'][f'L{lesson_id}P{part_id+1}'] = part_code


manager = tgalice.dialog_manager.CascadeDialogManager(
    tgalice.dialog_manager.AutomatonDialogManager(menu, matcher='cosine'),
    tgalice.dialog_manager.GreetAndHelpDialogManager(
        greeting_message="Дефолтное приветственное сообщение",
        help_message="Дефолтный вызов помощи",
        default_message='Я вас не понимаю.',
        exit_message='Всего доброго! Было приятно с вами пообщаться!'
    )
)

connector = tgalice.dialog_connector.DialogConnector(
    dialog_manager=manager,
    storage=tgalice.storage.session_storage.BaseStorage(),
    alice_native_state='state',
)

alice_handler = connector.serverless_alice_handler


if __name__ == '__main__':
    server = tgalice.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
