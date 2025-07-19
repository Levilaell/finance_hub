[ 9/10] RUN python manage.py collectstatic --noinput || true

Traceback (most recent call last):
  File "/app/manage.py", line 22, in <module>
    main()

  File "/app/manage.py", line 18, in main

    execute_from_command_line(sys.argv)
  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line

    utility.execute()

  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 382, in execute

    settings.INSTALLED_APPS
  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 89, in __getattr__

    self._setup(name)
  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 76, in _setup

    self._wrapped = Settings(settings_module)
           

      

   ^

^^^

^^^

^^^

^^^

^^^^

^^^

^^^^^

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 190, in __init__

    mod = importlib.import_module(self.SETTINGS_MODULE)

          ^

^^^^^^^^^^^^^^

^^^^^^^^^^^^^^^^

^^^^^

^^^^^^

^^^

  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module

    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^

^^^^^^^^^^^^^

^^^^^

^^^^^

^^^^

^^^^

^^

  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked

  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed

  File "/app/core/settings/production.py", line 19, in <module>

    SECRET_KEY = config('SECRET_KEY')

            

     ^

^^^

^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 248, in __call__

    return self.config(*args, **kwargs)
          

 ^^^^^^^

^^^

^^^^

^^

^^^^

^^

^^^^

^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 107, in __call__

    return self.get(*args, **kwargs)

           ^^^^^^^^^^^^^^^^

^^^^^^

^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 92, in get

    raise UndefinedValueError('{} not found. Declare it as envvar or define a default value.'.format(option))

decouple.UndefinedValueError: SECRET_KEY not found. Declare it as envvar or define a default value.

[ 9/10] RUN python manage.py collectstatic --noinput || true  ✔ 842 ms

[10/10] RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

[10/10] RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app  ✔ 623 ms

exporting to docker image format

exporting to image

[auth] sharing credentials for production-us-east4-eqdc4a.railway-registry.com

[auth] sharing credentials for production-us-east4-eqdc4a.railway-registry.com  ✔ 0 ms

importing to docker

importing to docker  ✔ 6 sec

Build time: 53.94 seconds

 

====================

Starting Healthcheck

====================


Path: /api/health/

Retry window: 5m0s

 

Attempt #1 failed with service unavailable. Continuing to retry for 4m49s

Attempt #2 failed with service unavailable. Continuing to retry for 4m48s

Attempt #3 failed with service unavailable. Continuing to retry for 4m46s

Attempt #4 failed with service unavailable. Continuing to retry for 4m42s

Attempt #5 failed with service unavailable. Continuing to retry for 4m34s

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 76, in _setup

    self._wrapped = Settings(settings_module)

                    ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 190, in __init__

    mod = importlib.import_module(self.SETTINGS_MODULE)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module

    return _bootstrap._gcd_import(name[level:], package, level)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import

  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load

  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked

  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked

  File "<frozen importlib._bootstrap_external>", line 940, in exec_module

  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed

  File "/app/core/settings/production.py", line 19, in <module>

    SECRET_KEY = config('SECRET_KEY')

                 ^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 248, in __call__

    return self.config(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 107, in __call__

    return self.get(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 92, in get

    raise UndefinedValueError('{} not found. Declare it as envvar or define a default value.'.format(option))

decouple.UndefinedValueError: SECRET_KEY not found. Declare it as envvar or define a default value.

Traceback (most recent call last):

  File "/app/manage.py", line 22, in <module>

    main()

  File "/app/manage.py", line 18, in main

    execute_from_command_line(sys.argv)

  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line

    utility.execute()

  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 382, in execute

    settings.INSTALLED_APPS

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 89, in __getattr__

    self._setup(name)

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 76, in _setup

    self._wrapped = Settings(settings_module)

                    ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 190, in __init__

    mod = importlib.import_module(self.SETTINGS_MODULE)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module

    return _bootstrap._gcd_import(name[level:], package, level)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

^^^^

  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed

  File "/app/core/settings/production.py", line 19, in <module>

    SECRET_KEY = config('SECRET_KEY')

                 ^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 248, in __call__

    return self.config(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 107, in __call__

    return self.get(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 92, in get

    raise UndefinedValueError('{} not found. Declare it as envvar or define a default value.'.format(option))

decouple.UndefinedValueError: SECRET_KEY not found. Declare it as envvar or define a default value.

Traceback (most recent call last):

  File "/app/manage.py", line 22, in <module>

    main()

  File "/app/manage.py", line 18, in main

    execute_from_command_line(sys.argv)

  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line

    utility.execute()

  File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 382, in execute

    settings.INSTALLED_APPS

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 89, in __getattr__

    self._setup(name)

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 76, in _setup

    self._wrapped = Settings(settings_module)

                    ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/django/conf/__init__.py", line 190, in __init__

    mod = importlib.import_module(self.SETTINGS_MODULE)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module

    return _bootstrap._gcd_import(name[level:], package, level)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

^^^^^^^^

  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import

  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load

  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked

  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked

  File "<frozen importlib._bootstrap_external>", line 940, in exec_module

  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed

  File "/app/core/settings/production.py", line 19, in <module>

    SECRET_KEY = config('SECRET_KEY')

                 ^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 248, in __call__

    return self.config(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 107, in __call__

    return self.get(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/decouple.py", line 92, in get

    raise UndefinedValueError('{} not found. Declare it as envvar or define a default value.'.format(option))

decouple.UndefinedValueError: SECRET_KEY not found. Declare it as envvar or define a default value.