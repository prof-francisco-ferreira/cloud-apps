import threading
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.watch import DocumentChange

# 1. Inicializar a conexão com o Firebase
# Certifique-se de que o arquivo serviceAccountKey.json está na mesma pasta
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print("Erro ao conectar ao Firebase. Verifique o arquivo serviceAccountKey.json.")
    print(f"Detalhe: {e}")
    exit()

# Flag para saber se é a primeira vez que carregamos as mensagens
# Isso evita que o chat exiba todo o histórico antigo de uma vez de forma confusa
is_first_load = True

# 2. Função que "escuta" o banco de dados em tempo real
def on_snapshot(col_snapshot, changes, read_time):
    global is_first_load
    
    for change in changes:
        # Só queremos mostrar as mensagens que foram ADICIONADAS
        if change.type.name == 'ADDED':
            mensagem = change.document.to_dict()
            remetente = mensagem.get('usuario', 'Desconhecido')
            texto = mensagem.get('texto', '')
            
            # Se não for a carga inicial (histórico), mostramos a mensagem na tela
            if not is_first_load:
                # Limpa a linha atual do input para não sobrepor o texto
                print(f"\r[{remetente}]: {texto}")
                print(f"[{meu_usuario}]: ", end="", flush=True)

    is_first_load = False

# 3. Interação com o usuário
print("="*40)
print("Bem-vindo ao Chat Python + Firebase!")
print("="*40)
meu_usuario = input("Digite seu nome de usuário para entrar: ")

print(f"\nConectando ao servidor da sala de chat... Aguarde.")

# 4. Configurar o Listener (Ouvinte) do Firebase
# Vamos ouvir a coleção 'mensagens', ordenando pela data de envio
colecao_mensagens = db.collection('mensagens').order_by('timestamp')
# Inicia a escuta em uma thread separada (não trava o programa)
query_watch = colecao_mensagens.on_snapshot(on_snapshot)

# Aguarda um segundinho para o listener baixar o histórico antes de liberar o input
time.sleep(2)

print("\nConectado! Você já pode enviar mensagens. (Digite '/sair' para encerrar)")
print("="*40)

# 5. Loop principal para enviar mensagens
while True:
    try:
        texto = input(f"[{meu_usuario}]: ")
        
        if texto.lower() == '/sair':
            print("Saindo do chat...")
            break
            
        if texto.strip(): # Só envia se não for vazio
            # Adiciona a mensagem ao Firestore
            db.collection('mensagens').add({
                'usuario': meu_usuario,
                'texto': texto,
                'timestamp': firestore.SERVER_TIMESTAMP # Data e hora do servidor Firebase
            })
    except KeyboardInterrupt:
        print("\nSaindo do chat...")
        break

# Encerrar o listener quando sair
query_watch.unsubscribe()