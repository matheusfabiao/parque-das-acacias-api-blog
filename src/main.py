import logging
from http import HTTPStatus

import httpx
from bs4 import BeautifulSoup
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.schemas import PostResponse
from src.settings import Settings

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Cria uma instância do FastAPI
app = FastAPI(
    title='API Blog Parque das Acácias',
    description='API para obter os posts do blog do Parque das Acácias',
    version='0.1.0',
)

# Instância da classe HTTPBearer
security = HTTPBearer()

# Instância da classe Settings
settings = Settings()

# Configura CORS (permite outros sites acessarem sua API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # TODO: Em produção, restringir aos domínios certos!
    allow_methods=['GET'],
)

# Variáveis de ambiente para WordPress
WP_URL = settings.WP_URL
WP_JWT_SECRET_KEY = settings.WP_JWT_SECRET_KEY
WP_LOGIN = settings.WP_LOGIN
WP_PASSWORD = settings.WP_PASSWORD


async def get_jwt_token_from_wp():
    """Obtém um token JWT da API WordPress.

    Returns:
        str: token JWT
    """
    logger.info('Obtendo token JWT da API WordPress')
    async with httpx.AsyncClient() as client:
        # Requisição POST para obter o token JWT
        try:
            response = await client.post(
                f'{WP_URL}/wp-json/jwt-auth/v1/token',
                json={'username': WP_LOGIN, 'password': WP_PASSWORD},
            )
            response.raise_for_status()
            logger.info('Token JWT obtido com sucesso')
            return response.json()['token']
        except httpx.HTTPError as e:
            logger.error(f'Erro na obtenção do token JWT: {str(e)}')
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Erro na obtenção do token JWT: {e}',
            )

# verificar se o token obtido da função get_jwt_token_from_wp é válido
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verifica se o token JWT é válido.

    Args:
        credentials (HTTPAuthorizationCredentials):
            credenciais de autenticação

    Returns:
        dict: token JWT
    """
    logger.info('Verificando token JWT')
    try:
        payload = jwt.decode(
            credentials.credentials,
            WP_JWT_SECRET_KEY,
            algorithms=['HS256'],
        )
        logger.info('Token JWT válido')
        return {'token': credentials.credentials, 'payload': payload}
    except JWTError as e:
        logger.error(f'Erro na verificação do token JWT: {str(e)}')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=f'Erro na verificação do token JWT: {e}',
        )
        

def get_headers(token: str = Depends(get_jwt_token_from_wp)):
    """Retorna os headers para a requisição.

    Returns:
        dict: headers
    """
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


# Função para remover tags HTML do resumo
def clean_html(html_content):
    """Remove tags HTML mantendo apenas o texto.

    Args:
        html_content (str): conteúdo HTML

    Returns:
        str: conteúdo sem tags HTML
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()


async def get_media_url(post_data, client, token: str = Depends(get_jwt_token_from_wp)):
    """Pega a URL da imagem destacada do post.

    Returns:
        str: URL da imagem destacada do post
    """
    logger.info(f'Buscando mídia para o post ID: {post_data["id"]}')
    media_response = await client.get(
        f'{WP_URL}/wp-json/wp/v2/media/{post_data["featured_media"]}',
        headers=get_headers(token),
        params={'_fields': 'guid.rendered'},  # URL da imagem
    )
    if media_response.status_code == HTTPStatus.OK:
        post_data['featured_media'] = (
            media_response.json().get('guid', {}).get('rendered')
        )
        logger.info(f'Mídia encontrada para o post ID: {post_data["id"]}')
    else:
        post_data['featured_media'] = None
        logger.warning(
            f'Mídia não encontrada para o post ID: {post_data["id"]}'
        )

    return post_data


# Função para buscar dados da API WordPress
async def fetch_wp_data(token: str = Depends(get_jwt_token_from_wp)):
    """Busca dados da API WordPress.

    Returns:
        list: lista de posts
    """
    try:
        logger.info('Iniciando busca de posts no WordPress')
        async with httpx.AsyncClient() as client:
            # Requisição GET para obter os dados dos posts
            response = await client.get(
                f'{WP_URL}/wp-json/wp/v2/posts',
                headers=get_headers(token),
                params={
                    'per_page': 3,  # Limita a 3 posts
                    '_fields': 'id,link,title,excerpt,featured_media',  # Otimiza a resposta
                },
            )
            # Verifica se a requisição foi bem-sucedida
            response.raise_for_status()

            # Retorna os dados dos posts em formato JSON
            posts = response.json()
            logger.info(f'Encontrados {len(posts)} posts')

            # Pegar a URL das imagens dos posts obtidos
            formatted_posts = []
            for post in posts:
                logger.info(f'Processando post ID: {post["id"]}')
                # Limpa o HTML do resumo do post
                clean_excerpt = clean_html(post['excerpt']['rendered'])

                # Formata os dados do post
                post_data = {
                    'id': post['id'],
                    'link': post['link'],
                    'title': post['title'],
                    'excerpt': clean_excerpt,
                    'featured_media': post['featured_media'],
                }

                # Se existir imagem destacada, busca a URL completa
                if post_data['featured_media']:
                    # Requisição GET para obter os dados da imagem
                    post_data = await get_media_url(post_data, client, token)

                formatted_posts.append(post_data)

            logger.info('Processamento de posts concluído com sucesso')
            return formatted_posts

    except httpx.HTTPError as e:
        logger.error(f'Erro ao buscar dados da API WordPress: {str(e)}')
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao buscar dados da API WordPress: {e}',
        )


# Rota para obter os dados dos posts
@app.get('/posts', response_model=list[PostResponse])
async def get_posts(auth_data: dict = Depends(verify_token)):
    logger.info('Requisição recebida na rota /posts')
    token = auth_data['token']
    # Retorna os dados dos posts em formato JSON com o token JWT no response
    return await fetch_wp_data(token)


# Rota raiz para verificar se a API está funcionando
@app.get('/')
async def root():
    logger.info('Verificação de status da API')
    return {'message': 'API Blog está funcionando!'}

@app.post('/auth')
async def auth():
    """Obtém um token JWT da API WordPress.

    Returns:
        dict: token JWT
    """
    token = await get_jwt_token_from_wp()
    return {'token': token}
