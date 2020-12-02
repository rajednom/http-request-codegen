
import multiprocessing
import os
import sys

import flask
import inflection
import pytest

from http_request_codegen.string import replace_multiple


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
if TEST_DIR not in sys.path:
    sys.path.append(TEST_DIR)

TEST_SERVER_HOST = 'localhost'
TEST_SERVER_PORT = '8876'
TEST_BASE_URL = 'http://%s:%s' % (TEST_SERVER_HOST, TEST_SERVER_PORT)


def values_list():
    return ['foo', 'bar', 'baz', 1, -1.5, True, False, None]


def value():
    return 'foo'


@pytest.fixture()
def assert_request_args():
    def _assert_request_args(request_args, response_args):
        # print('\nREQUEST ARGS: ', request_args)
        # print('RESPONSE ARGS:', response_args)

        if 'parameters' in request_args:
            for param in request_args['parameters']:
                assert param['name']
                assert isinstance(param['name'], str)

                _param_found = False
                for _param in response_args['parameters']:
                    if str(param['name']) == _param['name']:
                        _param_found = True
                        assert str(param['value']) == _param['value']

                        assert _param['name']
                        assert isinstance(_param['name'], str)
                        break
                assert _param_found

        if 'headers' in request_args:
            for hname, hvalue in request_args['headers'].items():
                assert hname
                assert isinstance(hname, str)
                assert hvalue
                assert isinstance(hvalue, str)

                assert hname in response_args['headers']
                assert hvalue == request_args['headers'][hname]
    return _assert_request_args


def on_start():
    # Setup Flask server in new process
    test_server = flask.Flask('http-request-codegen_tests')

    @test_server.route('/')
    def hello_world():
        return {
            'parameters': [
                {
                    'name': name,
                    'value': value
                } for name, value in flask.request.args.items()],
            'headers': {
                name: value for name, value in flask.request.headers.items()
            }
        }

    def flask_proc():
        test_server.run(host=TEST_SERVER_HOST,
                        port=TEST_SERVER_PORT,
                        debug=True,
                        use_reloader=False)

    proc = multiprocessing.Process(target=flask_proc, args=())
    proc.start()
    return proc


@pytest.fixture(autouse=True, scope='session')
def _session_fixture():
    proc = on_start()
    yield
    proc.terminate()


def argument_combination_to_filename(combination_name, index):
    return '%s.%s.expect.txt' % (
        str(index).zfill(3),
        inflection.parameterize(
            replace_multiple(combination_name, replacements={
                '"': '-double-quote-',
                '\'': '-single-quote-',
            })
        )
    )


def combination_arguments_to_kwargs(arguments):
    kwargs = {}
    for key, value in arguments.items():
        if key == 'kwargs':
            kwargs.update(value)
        else:
            kwargs[key] = value
    return kwargs


def get_argument_combinations(include_filenames=True, dirpath=None):
    response = [
        {
            'name': 'URL',
            'arguments': {
                'url': TEST_BASE_URL
            }
        },
        {
            'name': 'URL wrapping (no wrap)',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 99999
            }
        },
        {
            'name': 'URL wrapping (wrap 15)',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 15,
            }
        },
        {
            'name': 'URL + parameter',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    }
                ]
            }
        },
        {
            'name': 'URL + parameters',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'foo'
                    },
                    {
                        'name': 'param-2',
                        'value': 1
                    },
                    {
                        'name': 'param-3',
                        'value': .777
                    },
                    {
                        'name': 'param-4',
                        'value': True
                    },
                ]
            }
        },
        {
            'name': 'URL + parameter wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'foo-bar-baz' * 50,
                    }
                ]
            }
        },
        {
            'name': 'URL + parameters, one wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'foo-bar-baz' * 50,
                    },
                    {
                        'name': 'param-2',
                        'value': 'value-2'
                    }
                ]
            }
        },
        {
            'name': 'URL + parameter wrapping value smart spaces',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'Wrap me handling spaces smartly ' * 15,
                    }
                ]
            }
        },
        {
            'name': 'URL + parameter escaping quotes',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1-with-\'\'-quotes',
                        'value': 'value-1-with-\'\'-quotes'
                    }
                ]
            }
        },
        {
            'name': 'URL + header',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        },
        {
            'name': 'URL + headers',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': 'es',
                }
            }
        },
        {
            'name': 'URL + header wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json' * 5,
                }
            }
        },
        {
            'name': 'URL + headers, one wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json' * 5,
                    'Accept-Language': '*'
                }
            }
        },
        {
            'name': 'URL + header escaping quotes',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Accept-Language': 'Header value with \'\' quotes'
                }
            }
        },
        {
            'name': 'URL + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'kwargs': {
                    'timeout': 5,
                }
            }
        },
        {
            'name': 'URL + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'kwargs': {
                    'timeout': 5,
                    'stream': True
                }
            }
        },
        {
            'name': 'URL + kwarg escaping quotes',
            'arguments': {
                'url': TEST_BASE_URL,
                'kwargs': {
                    'cookies': {
                        'foo': 'value with \'\' quotes'
                    }
                }
            }
        },
        {
            'name': 'URL + kwarg wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'kwargs': {
                    'cookies': {
                        'bar': 'foo bar baz ' * 50
                    }
                }
            }
        },
        {
            'name': 'URL + kwargs, one wrapping value',
            'arguments': {
                'url': TEST_BASE_URL,
                'kwargs': {
                    'cookies': {
                        'bar': 'foo bar baz ' * 50
                    },
                    'stream': True
                }
            }
        },
        {
            'name': 'URL + parameter + header',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        },
        {
            'name': 'URL + parameters + header',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 'value-2'
                    },
                ],
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        },
        {
            'name': 'URL + parameter + headers',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': '*'
                }
            }
        },
        {
            'name': 'URL + parameters + headers',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 'value-2'
                    },
                ],
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': '*'
                }
            }
        },
        {
            'name': 'URL + parameter + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1',
                    }
                ],
                'kwargs': {
                    'timeout': 10
                }
            }
        },
        {
            'name': 'URL + parameters + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1',
                    },
                    {
                        'name': 'param-2',
                        'value': 'value-2',
                    }
                ],
                'kwargs': {
                    'timeout': 10
                }
            }
        },
        {
            'name': 'URL + parameter + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1',
                    }
                ],
                'kwargs': {
                    'timeout': 10,
                    'stream': True
                }
            }
        },
        {
            'name': 'URL + parameters + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1',
                    },
                    {
                        'name': 'param-2',
                        'value': 'value-2',
                    }
                ],
                'kwargs': {
                    'timeout': 10,
                    'stream': True
                }
            }
        },
        {
            'name': 'URL + header + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'kwargs': {
                    'timeout': 5
                }
            }
        },
        {
            'name': 'URL + headers + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': '*'
                },
                'kwargs': {
                    'timeout': 5
                }
            }
        },
        {
            'name': 'URL + header + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Accept-Language': '*'
                },
                'kwargs': {
                    'timeout': 5,
                    'stream': False
                }
            }
        },
        {
            'name': 'URL + headers + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': '*'
                },
                'kwargs': {
                    'timeout': 5,
                    'stream': False
                }
            }
        },
        {
            'name': 'URL + parameter + header + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json'
                },
                'kwargs': {
                    'timeout': 5
                }
            }
        },
        {
            'name': 'URL + parameter + header + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json'
                },
                'kwargs': {
                    'timeout': 5,
                    'stream': True
                }
            }
        },
        {
            'name': 'URL + parameters + header + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 7.77
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json'
                },
                'kwargs': {
                    'timeout': 5
                }
            }
        },
        {
            'name': 'URL + parameters + header + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 7.77
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json'
                },
                'kwargs': {
                    'timeout': 5,
                    'stream': False
                }
            }
        },
        {
            'name': 'URL + parameters + headers + kwarg',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 7.77
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': 'fr'
                },
                'kwargs': {
                    'timeout': 5
                }
            }
        },
        {
            'name': 'URL + parameters + headers + kwargs',
            'arguments': {
                'url': TEST_BASE_URL,
                'parameters': [
                    {
                        'name': 'param-1',
                        'value': 'value-1'
                    },
                    {
                        'name': 'param-2',
                        'value': 7.77
                    }
                ],
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept-Language': 'fr'
                },
                'kwargs': {
                    'timeout': 5,
                    'stream': True
                }
            }
        },
        {
            'name': 'No setup',
            'arguments': {
                'url': TEST_BASE_URL,
                'setup': False,
            }
        },
        {
            'name': 'Custom setup',
            'arguments': {
                'url': TEST_BASE_URL,
                'setup': 'custom_setup=1\n\n'
            }
        },
        {
            'name': 'Custom teardown',
            'arguments': {
                'url': TEST_BASE_URL,
                'teardown': '\n\ncustom_teardown=1'
            }
        },
        {
            'name': 'Quote character \'',
            'arguments': {
                'url': TEST_BASE_URL,
                'quote_char': '\''
            }
        },
        {
            'name': 'Quote character "',
            'arguments': {
                'url': TEST_BASE_URL,
                'quote_char': '"'
            }
        },
        {
            'name': 'Indent two spaces',
            'arguments': {
                'url': TEST_BASE_URL,
                'indent': '  ',
                'headers': {
                    'Accept-Language': 'es en fr * ' * 50,
                },
            }
        },
        {
            'name': 'Indent four spaces',
            'arguments': {
                'url': TEST_BASE_URL,
                'indent': '    ',
                'headers': {
                    'Accept-Language': 'es en fr * ' * 50,
                },
            }
        },
        {
            'name': 'Indent tab',
            'arguments': {
                'url': TEST_BASE_URL,
                'indent': '\t',
                'headers': {
                    'Accept-Language': 'es en fr * ' * 50,
                },
            }
        },
        {
            'name': 'One line',
            'arguments': {
                'url': TEST_BASE_URL,
                'oneline': True
            }
        },
        {
            'name': 'One line + no setup',
            'arguments': {
                'url': TEST_BASE_URL,
                'oneline': True,
                'setup': False
            }
        },
        {
            'name': 'Wrap 0',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 0
            }
        },
        {
            'name': 'Wrap 1',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 1
            }
        },
        {
            'name': 'Wrap 10',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 10
            }
        },
        {
            'name': 'Wrap 20',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 20
            }
        },
        {
            'name': 'Wrap 30',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 30
            }
        },
        {
            'name': 'Wrap 35',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 35
            }
        },
        {
            'name': 'Wrap 40',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': 40
            }
        },
        {
            'name': 'Wrap infinite',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': float('inf')
            }
        },
        {
            'name': 'Wrap null is infinite',
            'arguments': {
                'url': TEST_BASE_URL,
                'wrap': None
            }
        }
    ]

    if include_filenames:
        for index, args_group in enumerate(response):
            fname = argument_combination_to_filename(
                args_group['name'], index)
            if dirpath and os.path.exists(dirpath):
                fname = os.path.join(dirpath, fname)
            args_group['filename'] = fname
    return response
