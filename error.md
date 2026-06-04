[AUTH] ALLOW score=0.6675 margin=0.6675 latency=0.2ms
ERROR: Exception in ASGI application
Traceback (most recent call last):
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\uvicorn\protocols\websockets\websockets_impl.py", line 240, in run_asgi
result = await self.app(self.scope, self.asgi_receive, self.asgi_send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\uvicorn\middleware\proxy_headers.py", line 69, in **call**
return await self.app(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\fastapi\applications.py", line 1054, in **call**
await super().**call**(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\applications.py", line 123, in **call**
await self.middleware_stack(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\middleware\errors.py", line 151, in **call**
await self.app(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\middleware\cors.py", line 77, in **call**
await self.app(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\middleware\exceptions.py", line 65, in **call**
await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette_exception_handler.py", line 64, in wrapped_app
raise exc
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette_exception_handler.py", line 53, in wrapped_app
await app(scope, receive, sender)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\routing.py", line 756, in **call**
await self.middleware_stack(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\routing.py", line 776, in app
await route.handle(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\routing.py", line 373, in handle
await self.app(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\routing.py", line 96, in app
await wrap_app_handling_exceptions(app, session)(scope, receive, send)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette_exception_handler.py", line 64, in wrapped_app
raise exc
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette_exception_handler.py", line 53, in wrapped_app
await app(scope, receive, sender)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\starlette\routing.py", line 94, in app
await func(session)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\venv\lib\site-packages\fastapi\routing.py", line 348, in app
await dependant.call(\*\*values)
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\routers\verify.py", line 182, in ws_verify
await broadcast_alert({
File "C:\Users\Mrlhou\Desktop\lab_access_system\server\routers\alerts.py", line 99, in broadcast_alert
for client in alert_clients:
UnboundLocalError: local variable 'alert_clients' referenced before assignment
