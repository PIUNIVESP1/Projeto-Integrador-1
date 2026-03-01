from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask(__name__)
DATABASE = 'banco.db'
MERCADOS = ['ASSAÍ', 'CARREFOUR', 'MAX']

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        # Cria tabela se não existir
        db.execute('''
            CREATE TABLE IF NOT EXISTS precos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT NOT NULL,
                mercado TEXT NOT NULL,
                preco REAL NOT NULL,
                UNIQUE(produto, mercado) ON CONFLICT REPLACE
            )
        ''')
        db.commit()

# --- ROTAS ---

@app.route('/')
def index():
    db = get_db()
    # Busca todos os registros
    cursor = db.execute('SELECT * FROM precos ORDER BY produto')
    dados = cursor.fetchall()
    
    # Organiza os dados para fácil exibição na tabela
    # Estrutura: produtos[nome_produto] = {'ASSAÍ': 10.0, 'MAX': 12.0 ...}
    tabela_comparativa = {}
    
    for linha in dados:
        prod = linha['produto']
        mercado = linha['mercado']
        preco = linha['preco']
        
        if prod not in tabela_comparativa:
            tabela_comparativa[prod] = {m: None for m in MERCADOS} # Inicializa tudo vazio
        
        tabela_comparativa[prod][mercado] = preco

    return render_template('index.html', tabela=tabela_comparativa, mercados=MERCADOS)

@app.route('/atualizar', methods=['GET', 'POST'])
def atualizar():
    if request.method == 'POST':
        produto = request.form['produto'].upper().strip()
        mercado = request.form['mercado']
        preco = float(request.form['preco'].replace(',', '.')) # Aceita vírgula ou ponto
        
        db = get_db()
        # O SQL usa 'OR REPLACE' para atualizar se já existir ou inserir se for novo
        db.execute('INSERT OR REPLACE INTO precos (produto, mercado, preco) VALUES (?, ?, ?)',
                   (produto, mercado, preco))
        db.commit()
        return redirect(url_for('index'))
    
    return render_template('atualizar.html', mercados=MERCADOS)

if __name__ == '__main__':
    init_db() # Cria o banco ao iniciar
    app.run(debug=True)