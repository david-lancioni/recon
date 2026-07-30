from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask.sessions import SessionInterface, SecureCookieSession

REQUEST_HEADER = 'Authorization'
RESPONSE_HEADER = 'X-Auth-Token'
TOKEN_SALT = 'recon-auth-token'
TOKEN_MAX_AGE = 8 * 60 * 60


class TokenSessionInterface(SessionInterface):
    """Sessão baseada em token assinado (header), não em cookie.

    Cada aba/janela guarda o próprio token em sessionStorage, então múltiplas
    abas do mesmo navegador deixam de compartilhar login/empresa — ao contrário
    do cookie de sessão padrão do Flask, que é o mesmo em todas as abas.
    """

    def _serializer(self, app):
        return URLSafeTimedSerializer(app.secret_key, salt=TOKEN_SALT)

    def _extract_token(self, request):
        auth = request.headers.get(REQUEST_HEADER, '')
        if auth.startswith('Bearer '):
            return auth[len('Bearer '):].strip() or None
        return None

    def open_session(self, app, request):
        token = self._extract_token(request)
        if not token:
            return SecureCookieSession()
        try:
            data = self._serializer(app).loads(token, max_age=TOKEN_MAX_AGE)
        except (BadSignature, SignatureExpired):
            return SecureCookieSession()
        if not isinstance(data, dict):
            return SecureCookieSession()
        return SecureCookieSession(data)

    def save_session(self, app, session, response):
        if not session.modified:
            return
        data = dict(session)
        if not data:
            return
        token = self._serializer(app).dumps(data)
        response.headers[RESPONSE_HEADER] = token
