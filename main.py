import streamlit as st
from azure.storage.blob import BlobServiceClient
import os 
import pymssql
import uuid
import json
from dotenv import load_dotenv
load_dotenv()

blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

st.title("Cadastro de Produtos")


#formulário de cadastro de produtos
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])

#Save image on blob storage
def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)

    # Upload the file to Azure Blob Storage
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

def insert_product(name, price, description, product_image):
    try:
        image_url = upload_blob(product_image)
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USERNAME, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dbo.Produtos (nome, preco, descricao, image_url) VALUES (%s, %s, %s, %s)", (name, price, description, image_url))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao fazer upload da imagem e/ou inserir produto: {e}")
        return False    

def list_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USERNAME, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.Produtos")
        columns = [column[0] for column in cursor.description]  # Obter nomes das colunas
        products = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Converter tuplas em dicionários
        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []
    
def list_products_screen():
    products = list_products()
    if products:
        cards_por_linhas = 3
        colunas = st.columns(cards_por_linhas)
        for i, product in enumerate(products):
            with colunas[i % cards_por_linhas]:
                st.markdown(f"### {product['nome']}")  # Nome do produto
                st.write(f"**Descrição:** {product['descricao']}")  # Descrição
                st.write(f"**Preço:** R$ {product['preco']}")  # Preço
                if product.get('image_url'):  # URL da imagem
                    html_img = f'<img src="{product["image_url"]}" alt="Imagem do Produto" width="200" height="200">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")
            if (i + 1) % cards_por_linhas == 0 and i < len(products) - 1:
                colunas = st.columns(cards_por_linhas)
    else:
        st.write("Nenhum produto cadastrado.")

if st.button('Salvar Produto'):
    insert_product(product_name, product_price, product_description, product_image)
    if product_image is not None:
        st.success("Produto salvo com sucesso!")
    else:
        st.error("Erro ao salvar o produto. Verifique os dados e tente novamente.")
    return_message = 'Produto salvo com sucesso'

st.header("Produtos Cadastrados")

if st.button('Listar Produtos'):
    list_products_screen()
    return_message = 'Produtos listados com sucesso'

# Test database connection
try:
    conn = pymssql.connect(server=SQL_SERVER, user=SQL_USERNAME, password=SQL_PASSWORD, database=SQL_DATABASE)
    st.success("Conexão com o banco de dados bem-sucedida!")
    conn.close()
    list_products_screen()
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
