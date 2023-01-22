from datetime import datetime
from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__) # Inicialização da Aplicação WEB
conexao = mysql.connector.connect(
    host='localhost',
    user='root',
    password='passwordsql',
    database='app_uniasselvi'
)

cursor = conexao.cursor()

# Página de Login
@app.route('/', methods=['GET', 'POST'])
def home():
    global usuario, senha, id_aluno, nome_aluno, usuario_aluno, senha_aluno, tipo_aluno, lista_alunos, lista_avaliacoes, lista_provas
    
    # Coletando usuário e senha preenchidos no formulário
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        print(usuario)
        print(senha)
    else:
        usuario = None
        senha = None

    # Coletando lista dos USUÁRIOS cadastrados no Banco de Dados para realizar validação
    comando = f'SELECT * FROM aluno'
    cursor.execute(comando)
    lista_alunos = cursor.fetchall()

    # Coletando lista das AVALIAÇÕES realizadas no Banco de Dados para realizar validação
    comando = f'SELECT * FROM avaliacao'
    cursor.execute(comando)
    lista_avaliacoes = cursor.fetchall()

    # Coletando lista das PROVAS realizadas no Banco de Dados para realizar validação
    comando = f'SELECT * FROM prova'
    cursor.execute(comando)
    lista_provas = cursor.fetchall()

    # Validação do Usuário e Senha inseridos na page Home
    if usuario != None and senha != None:
        for user in lista_alunos:
            if user[2] == usuario and user[3] == senha:
                id_aluno = user[0]
                nome_aluno = user[1]
                usuario_aluno = user[2]
                senha_aluno = user[3]
                tipo_aluno = user[4]

                if tipo_aluno == 'Administrador': # Acesso adiministrador
                    return render_template('pageadmin.html', lista_alunos=lista_alunos, lista_avaliacoes=lista_avaliacoes, lista_provas=lista_provas)
                else: # Caso o login for válido, será redirecionado para a página de aluno
                    # primeiro_nome = nome_aluno[:nome_aluno.find(' '):] # Para pegar apenas o primeiro nome do aluno

                    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, tipo_aluno=tipo_aluno)
        else: # Caso o Usuário e Senha não possuam no Banco de Dados é retornado a mensagem de Login inválido
            incorreto = True
            msg = 'Login inválido, tente novamente!'
            return render_template('home.html', incorreto=incorreto, msg=msg)

    # Acessando a página pela primeira vez
    return render_template('home.html')

@app.route('/pageadmin', methods=['GET', 'POST'])
def pageadmin():
    home()

    return render_template('pageadmin.html', lista_alunos=lista_alunos, lista_avaliacoes=lista_avaliacoes, lista_provas=lista_provas)

@app.route('/pagealuno', methods=['GET', 'POST'])
def pagealuno():
    home()

    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, tipo_aluno=tipo_aluno)

# Função para deletar os cadastros realizados
@app.route('/deletar/<int:id>') # Exclusão é realizado com a coleta do ID do cadastro
def deletar(id):
    comando = f'DELETE FROM aluno WHERE id = {id};'
    cursor.execute(comando)
    conexao.commit()

    return redirect('/pageadmin') # Redirecionado para a Página Inicial

# Função de Atualizar cadastro do aluno
@app.route('/atualizar/<int:id>', methods=['GET', 'POST'])
def atualizar(id): 
    print(tipo_aluno)
    comando = f'SELECT * FROM aluno'
    cursor.execute(comando)
    lista_alunos = cursor.fetchall()

    # Identificando pelo ID, qual cadastro será atualizado
    for id_aluno in lista_alunos:
        if id == id_aluno[0]:
            aluno = id_aluno
            print(aluno)

    # Condição IF para redirecionar para a página correta.
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário

        att_nome = request.form.get('nome')
        att_usuario = request.form.get('usuario')
        att_senha = request.form.get('senha')

        if tipo_aluno == 'Aluno':
            att_tipo = 'Aluno'
        else:
            att_tipo = request.form.get('tipo')

        # Atualizando informações no Banco de Dados
        print('Atualizando...')
        comando = f'''UPDATE aluno SET nome = "{att_nome}", usuario = "{att_usuario}", senha = "{att_senha}", tipo = "{att_tipo}" WHERE id = {id};'''
        cursor.execute(comando)
        conexao.commit()

        if tipo_aluno == 'Administrado':
            return render_template('pageadmin.html', lista_alunos=lista_alunos, lista_avaliacoes=lista_avaliacoes)
        else:
            return render_template('pagealuno.html', att_nome=att_nome)
    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        if tipo_aluno == 'Administrador':
            return render_template('upgrade.html', aluno=aluno)
        elif tipo_aluno == 'Aluno':
            return render_template('upgradealuno.html', aluno=aluno)

# Função para transformar para tipo Float
def tipo_float(nota):
    nota = nota.replace(',','.') # Números decimais no Python são com "." Ponto e não com vírgula ",", dessa forma é realizado a substituição da pontuação e transformado em tipo float

    return float(nota)

# Função de coleto e tratamento de dados do formulário HTML CADASTRAR USUÁRIO
@app.route('/cadastrousuario', methods=['GET', 'POST'])
def cadastrousuario():
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário
        novo_nome = request.form.get('nome')
        novo_usuario = request.form.get('usuario')
        nova_senha = request.form.get('senha')
        novo_tipo = request.form.get('tipo')

        # Adicionando as variáveis a Classe Aluno
        comando = f'''INSERT INTO aluno (nome, usuario, senha, tipo)
            VALUES ("{novo_nome}", "{novo_usuario}", "{nova_senha}", "{novo_tipo}");'''
        cursor.execute(comando)
        conexao.commit()

        return redirect('pageadmin')
    else:
        return render_template('cadastrousuario.html')

# Função de coleta e tratamento de dados do formulário HTML CADASTRAR AVALIAÇÃO
def coletar_dados():
    global nome, data_nascimento, disciplina, hora, nota1, nota2, nota3, nota4, simulado, media # Indicando que essas variáveis são globais para ser utilizadas em qualquer função do código

    # Coletando nome do formulário HTML
    nome = request.form['nome']

    # Formatando a data para Dia/Mês/Ano
    data_nascimento = request.form['data_nascimento']
    dia = data_nascimento[8:10]
    mes = data_nascimento[5:7]
    ano = data_nascimento[0:4]
    data_nascimento = f'{dia}/{mes}/{ano}'

    # Coletando a escola do formulário HTML
    disciplina = request.form['disciplina']

    # Coletando data atual do registro realizado
    hora = datetime.today().strftime('%d/%m/%Y %H:%M:%S')

    # Coleta das Notas
    nota1 = tipo_float(request.form['nota1']) # Nota da Avaliação 1 (Peso 1.5)
    nota2 = tipo_float(request.form['nota2']) # Nota da Avaliação 2 (Peso 1.5)
    nota3 = tipo_float(request.form['nota3']) # Nota da Avaliação 3 (Peso 4)
    nota4 = tipo_float(request.form['nota4']) # Nota da Avaliação 4 (Peso 3)
    simulado = tipo_float(request.form['simulado']) # Nota do Simulado

    # Trantando notas para tipo float
    media = round(((((nota1*1.5) + (nota2*1.5) + (nota3*4) + (nota4*3)) / 10) + simulado),2) # Média das notas

# Prova
@app.route('/prova', methods=['GET','POST'])
def prova():
    global resposta1, resposta2, disciplina_selecionada

    disciplina_selecionada = request.form.get('prova')

    # Coletando a lista com todos os registros do Bando de Dados
    comando = f'SELECT * FROM prova'
    cursor.execute(comando)
    lista_prova = cursor.fetchall()         
    
    for prova in lista_prova:
        if prova[1] == disciplina_selecionada:
            resposta1 = prova[7]
            resposta2 = prova[13]

            return render_template('prova.html', prova=prova)

# Coletando respostas da avaliação
@app.route('/finalizarprova', methods=['GET','POST'])
def finalizarprova():
    nota_final = 0

    if request.method == 'POST':
        questao1 = request.form.get('questao1')
        questao2 = request.form.get('questao2')

        # Validando se a resposta foi certa ou errada QUESTÃO 01
        if questao1 == resposta1:
            nota1 = 'Certo'
            nota_final += 5
        else:
            nota1 = 'Errado'

        # Validando se a resposta foi certa ou errada QUESTÃO 02
        if questao2 == resposta2:
            nota2 = 'Certo'
            nota_final += 5
        else:
            nota2 = 'Errado'


        # Coletando data atual do registro realizado
        hora = datetime.today().strftime('%d/%m/%Y %H:%M:%S')

        # Adicionando as variáveis a Banco de Dados Avaliação
        comando = f'''INSERT INTO avaliacao (aluno, hora_avaliacao, disciplina, nota1, nota2, nota_final)
            VALUES ("{nome_aluno}", "{hora}", "{disciplina_selecionada}", "{nota1}", "{nota2}", "{nota_final}");'''
        cursor.execute(comando)
        conexao.commit()

    home()

    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, tipo_aluno=tipo_aluno)

# Alterar Avaliação realizada
@app.route('/atualizaravaliacao/<int:id>', methods=['GET', 'POST'])
def atualizaravaliacao(id): 
    comando = f'SELECT * FROM avaliacao'
    cursor.execute(comando)
    lista_avaliacao = cursor.fetchall()

    # Identificando pelo ID, qual avaliação será atualizado
    for id_avaliacao in lista_avaliacao:
        if id == id_avaliacao[0]:
            avaliacao = id_avaliacao
            print(avaliacao)

    # Condição IF para redirecionar para a página correta.
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário
        nota_final = 0

        att_nota1 = request.form.get('nota1')
        att_nota2 = request.form.get('nota2')

        # Validando se a resposta foi certa ou errada QUESTÃO 01
        if att_nota1 == 'Certo' and att_nota2 == 'Certo':
            nota_final = 10
        elif att_nota1 == 'Certo' or att_nota2 == 'Certo':
            nota_final = 5
        else:
            nota_final = 0

        # Atualizando informações no Banco de Dados
        print('Atualizando...')
        comando = f'''UPDATE avaliacao SET nota1 = "{att_nota1}", nota2 = "{att_nota2}", nota_final = "{nota_final}" WHERE id = {id};'''
        cursor.execute(comando)
        conexao.commit()
        
        return redirect('/pageadmin')

    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        return render_template('upgradeprova.html', avaliacao=avaliacao)

# Deletar os Avaliação realizados
@app.route('/deletaravaliacao/<int:id>') # Exclusão é realizado com a coleta do ID do cadastro
def deletaravaliacao(id):
    comando = f'DELETE FROM avaliacao WHERE id = {id};'
    cursor.execute(comando)
    conexao.commit()

    return redirect('/pageadmin') # Redirecionado para a Página Inicial

# Linha de código padrão para execução
if __name__ == '__main__':
    app.run(debug=False)