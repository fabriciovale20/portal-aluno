from datetime import datetime
from flask import Flask, render_template, request, redirect
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import psycopg2
import keybd as key

app = Flask(__name__) # Inicialização da Aplicação WEB

# BANCO DE DADOS MYSQL LOCAL
# conexao = mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='passwordsql',
#     database='app_uniasselvi'
# )

# BANCO DE DADOS POSTGRESQL
conexao = psycopg2.connect(
    host = key.KEYHOST,
    port = key.KEYPORT,
    user = key.KEYUSER,
    password = key.KEYPASSWORD,
    database = key.KEYDATABASE,
)

cursor = conexao.cursor()

####### PÁGINA LOGIN #######
@app.route('/', methods=['GET', 'POST'])
def home():
    global usuario, senha, id_aluno, nome_aluno, sexo_aluno, usuario_aluno, senha_aluno, email_aluno, tipo_aluno, lista_alunos, lista_avaliacoes, lista_provas, provas_disponiveis
    
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

    provas_disponiveis = []
    for nome_disciplina_avaliacao in lista_provas:
        provas_disponiveis.append(nome_disciplina_avaliacao)

    # Validação do Usuário e Senha inseridos na page Home
    if usuario != None and senha != None:
        for user in lista_alunos:
            if user[3] == usuario and user[4] == senha:
                id_aluno = user[0]
                nome_aluno = user[1]
                sexo_aluno = user[2]
                usuario_aluno = user[3]
                senha_aluno = user[4]
                email_aluno = user[5]
                tipo_aluno = user[7]

                if tipo_aluno == 'Administrador': # Acesso adiministrador
                    return render_template('pageadmin.html', lista_alunos=lista_alunos, lista_avaliacoes=lista_avaliacoes, lista_provas=lista_provas)
                else: # Caso o login for válido, será redirecionado para a página de aluno
                    # primeiro_nome = nome_aluno[:nome_aluno.find(' '):] # Para pegar apenas o primeiro nome do aluno

                    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, sexo_aluno=sexo_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, email_aluno=email_aluno, tipo_aluno=tipo_aluno, provas_disponiveis=provas_disponiveis)
        else: # Caso o Usuário e Senha não possuam no Banco de Dados é retornado a mensagem de Login inválido
            incorreto = True
            msg = 'Login inválido, tente novamente!'
            return render_template('home.html', incorreto=incorreto, msg=msg)

    # Acessando a página pela primeira vez
    return render_template('home.html')

####### OPÇÃO REGISTRAR-SE #######
@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    comando = f'SELECT * FROM aluno'
    cursor.execute(comando)
    lista_alunos = cursor.fetchall()

    if request.method == 'POST':
        nome_registrar = request.form.get('nome')
        sexo_registrar = request.form.get('sexo')
        usuario_registrar = request.form.get('usuario')
        senha_registrar = request.form.get('senha')
        confirmar_senha_registrar = request.form.get('confirmar_senha')
        email_registrar = request.form.get('email')

        # Coletando data atual do registro realizado
        data_registro_registrar = datetime.today().strftime('%d/%m/%Y %H:%M:%S')

        # Por padrão todo novo usuário é registrado como tipo Aluno
        tipo_registro = 'Aluno'

        erro_senha = ''
        erro_usuario = ''
        erro_email = ''
        
        # Validando se a senhas conferem
        if senha_registrar != confirmar_senha_registrar:
            erro_senha = 'As senhas não são iguais.'
            print(f'Erro Senha: {erro_senha}')

            return render_template('registrarse.html', erro_senha=erro_senha)

        else:
            for user in lista_alunos:
            # Validando se o usuário já está sendo utilizado
                if usuario_registrar == user[3]:
                    erro_usuario = 'Usuário já utilizado'
                    print(f'Erro Usuário: {erro_usuario}')

                    return render_template('registrarse.html', erro_usuario=erro_usuario)
                # Validando se o E-mail já está sendo utilizado
                elif email_registrar in user[5]:
                    erro_email = 'E-mail já utilizado'
                    print(f'Erro E-mail: {erro_email}')

                    return render_template('registrarse.html', erro_email=erro_email)

        # Adicionando as variáveis a Classe Aluno
        comando = f"""INSERT INTO aluno (nome, sexo, usuario, senha, email, dia_cadastro, tipo)
            VALUES ('{nome_registrar}', '{sexo_registrar}','{usuario_registrar}', '{senha_registrar}', '{email_registrar}',
            '{data_registro_registrar}','{tipo_registro}');"""
        cursor.execute(comando)
        conexao.commit()

        return redirect('/')
    else:
        return render_template('registrarse.html', lista_alunos=lista_alunos)

####### OPÇÃO ESQUECEU SENHA #######
@app.route('/esqueceusenha', methods=['GET', 'POST'])
def esqueceusenha():
    if request.method == 'POST':
        recuperar_senha = request.form.get('email')

        comando = f'SELECT * FROM aluno'
        cursor.execute(comando)
        lista_alunos = cursor.fetchall()

        # Validando se o E-mail que foi preenchido está cadastrado em algum usuário
        for buscar_senha in lista_alunos:
            if recuperar_senha == buscar_senha[5]:
                
                senha_atual = buscar_senha[4]
                nome_atual = buscar_senha[1]

                # Corpo da mensagem do Em=mail
                msg = MIMEMultipart()
                message = f'''Olá {nome_atual}!\nEsqueceu sua senha?\n\n Estamos aqui para lhe ajudar.\n\n Sua senha é: {senha_atual}'''

                # Credenciais e assunto do E-mail
                password = "pttoqroxvpeviwot"
                msg['From'] = 'fabriciovale18@gmail.com'
                msg['To'] = f'{recuperar_senha}'
                msg['Subject'] = 'Recuperação de Senha APP UNIASSELVI' # Assunto do E-mail

                # Monta conexão e envia o E-mail
                msg.attach(MIMEText(message, 'plain'))
                server = smtplib.SMTP('smtp.gmail.com', port=587)
                server.starttls()
                server.login(msg['From'], password)
                server.sendmail(msg['From'], msg['To'], msg.as_string())
                server.quit()

                return render_template('esqueceusenhaenviado.html')
        else:
            erro = 'E-mail não cadastrado!'
            return render_template('esqueceusenha.html', erro=erro)
            
    return render_template('esqueceusenha.html')

####### PÁGINA ADMINISTRADO #######
@app.route('/pageadmin', methods=['GET', 'POST'])
def pageadmin():
    home()

    return render_template('pageadmin.html', lista_alunos=lista_alunos, lista_avaliacoes=lista_avaliacoes, lista_provas=lista_provas)

####### PÁGINA ALUNO #######
@app.route('/pagealuno', methods=['GET', 'POST'])
def pagealuno():
    home()

    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, sexo_aluno=sexo_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, email_aluno=email_aluno, tipo_aluno=tipo_aluno, provas_disponiveis=provas_disponiveis)

####### USUÁRIO #######
# CADASTRAR
@app.route('/cadastrousuario', methods=['GET', 'POST'])
def cadastrousuario():
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário
        novo_nome = request.form.get('nome')
        novo_sexo = request.form.get('sexo')
        novo_usuario = request.form.get('usuario')
        nova_senha = request.form.get('senha')
        nova_email = request.form.get('email')
        novo_tipo = request.form.get('tipo')

        # Adicionando as variáveis a Classe Aluno
        comando = f"""INSERT INTO aluno (nome, sexo, usuario, senha, email, tipo)
            VALUES ('{novo_nome}', '{novo_sexo}', '{novo_usuario}', '{nova_senha}', '{nova_email}', '{novo_tipo}');"""
        cursor.execute(comando)
        conexao.commit()

        return redirect('pageadmin')
    else:
        return render_template('cadastrousuario.html')

# ATUALIZAR
@app.route('/atualizarusuario/<int:id>', methods=['GET', 'POST'])
def atualizarusuario(id): 
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
        att_sexo = request.form.get('sexo')
        att_usuario = request.form.get('usuario')
        att_senha = request.form.get('senha')
        att_email = request.form.get('email')

        if tipo_aluno == 'Aluno':
            att_tipo = 'Aluno'
        else:
            att_tipo = request.form.get('tipo')

        # Atualizando informações no Banco de Dados
        print('Atualizando...')
        comando = f"""UPDATE aluno SET nome = '{att_nome}', sexo = '{att_sexo}', usuario = '{att_usuario}', senha = '{att_senha}', email = '{att_email}', tipo = '{att_tipo}' WHERE id = {id};"""
        cursor.execute(comando)
        conexao.commit()
        
        if tipo_aluno == 'Administrador':
            return redirect('/pageadmin')
        else:
            return redirect('/pagealuno')
    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        if tipo_aluno == 'Administrador':
            return render_template('upgrade.html', aluno=aluno)
        elif tipo_aluno == 'Aluno':
            return render_template('upgradealuno.html', aluno=aluno)

# DELETAR
@app.route('/deletarusuario/<int:id>') # Exclusão é realizado com a coleta do ID do cadastro
def deletarusuario(id):
    comando = f'DELETE FROM aluno WHERE id = {id};'
    cursor.execute(comando)
    conexao.commit()

    return redirect('/pageadmin') # Redirecionado para a Página Inicial

####### HISTÓRICO DE AVALIAÇÃO #######
# ALTERAR
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
        comando = f"""UPDATE avaliacao SET nota1 = '{att_nota1}', nota2 = '{att_nota2}', nota_final = '{nota_final}' WHERE id = {id};"""
        cursor.execute(comando)
        conexao.commit()
        
        return redirect('/pageadmin')

    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        return render_template('alteraravaliacao.html', avaliacao=avaliacao)

# DELETAR
@app.route('/deletaravaliacao/<int:id>') # Exclusão é realizado com a coleta do ID do cadastro
def deletaravaliacao(id):
    comando = f'DELETE FROM avaliacao WHERE id = {id};'
    cursor.execute(comando)
    conexao.commit()

    return redirect('/pageadmin') # Redirecionado para a Página Inicial

# COLETANDO PROVA ESCOLHIDA
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

# COLETANDO RESPOSTAS DA AVALIAÇÃO REALIZADA
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
        comando = f"""INSERT INTO avaliacao (aluno, hora_avaliacao, disciplina, nota1, nota2, nota_final)
            VALUES ('{nome_aluno}', '{hora}', '{disciplina_selecionada}', '{nota1}', '{nota2}', '{nota_final}');"""
        cursor.execute(comando)
        conexao.commit()

    home()

    return render_template('pagealuno.html', id_aluno=id_aluno, nome_aluno=nome_aluno, usuario_aluno=usuario_aluno, senha_aluno=senha_aluno, email_aluno=email_aluno, tipo_aluno=tipo_aluno, provas_disponiveis=provas_disponiveis)

####### PROVAS CADASTRADAS #######
# CADASTRAR
@app.route('/cadastrarprova', methods=['GET', 'POST'])
def cadastrarprova(): 
    # Condição IF para redirecionar para a página correta.
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário

        disciplina = request.form.get('disciplina')
        questao1 = request.form.get('questao1')
        alternativa_a1 = request.form.get('alternativa_a1')
        alternativa_b1 = request.form.get('alternativa_b1')
        alternativa_c1 = request.form.get('alternativa_c1')
        alternativa_d1 = request.form.get('alternativa_d1')
        gabarito1 = request.form.get('gabarito1')

        questao2 = request.form.get('questao2')
        alternativa_a2 = request.form.get('alternativa_a2')
        alternativa_b2 = request.form.get('alternativa_b2')
        alternativa_c2 = request.form.get('alternativa_c2')
        alternativa_d2 = request.form.get('alternativa_d2')
        gabarito2 = request.form.get('gabarito2')

        # Atualizando informações no Banco de Dados
        print('Cadastrando...')
        comando = f"""INSERT INTO prova (disciplina, questao1, a1, b1, c1, d1, resposta1, questao2, a2, b2, c2, d2, resposta2)
            VALUES ('{disciplina}', '{questao1}', '{alternativa_a1}', '{alternativa_b1}', '{alternativa_c1}', '{alternativa_d1}', '{gabarito1}',
            '{questao2}', '{alternativa_a2}', '{alternativa_b2}', '{alternativa_c2}', '{alternativa_d2}', '{gabarito2}');"""
        cursor.execute(comando)
        conexao.commit()

        return redirect('/pageadmin')
    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        return render_template('cadastrarprova.html')

# ATUALIZAR
@app.route('/atualizarprova/<int:id>', methods=['GET', 'POST'])
def atualizarprova(id): 
    comando = f'SELECT * FROM prova'
    cursor.execute(comando)
    lista_provas = cursor.fetchall()

    # Identificando pelo ID, qual cadastro será atualizado
    for id_prova in lista_provas:
        if id == id_prova[0]:
            prova = id_prova

    # Condição IF para redirecionar para a página correta.
    if request.method == 'POST': # POST é quando o usuário solicita ao Banco de Dados que seja alterado alguma informação por meio da requisição do formulário

        att_disciplina = request.form.get('disciplina')
        att_questao1 = request.form.get('questao1')
        att_alternativa_a1 = request.form.get('alternativa_a1')
        att_alternativa_b1 = request.form.get('alternativa_b1')
        att_alternativa_c1 = request.form.get('alternativa_c1')
        att_alternativa_d1 = request.form.get('alternativa_d1')
        att_gabarito1 = request.form.get('gabarito1')

        att_questao2 = request.form.get('questao2')
        att_alternativa_a2 = request.form.get('alternativa_a2')
        att_alternativa_b2 = request.form.get('alternativa_b2')
        att_alternativa_c2 = request.form.get('alternativa_c2')
        att_alternativa_d2 = request.form.get('alternativa_d2')
        att_gabarito2 = request.form.get('gabarito2')

        # Atualizando informações no Banco de Dados
        print('Atualizando...')
        comando = f"""UPDATE prova SET disciplina = '{att_disciplina}',
        questao1 = '{att_questao1}', a1 = '{att_alternativa_a1}', b1 = '{att_alternativa_b1}', c1 = '{att_alternativa_c1}', d1 = '{att_alternativa_d1}', resposta1 = '{att_gabarito1}', 
        questao2 = '{att_questao2}', a2 = '{att_alternativa_a2}', b2 = '{att_alternativa_b2}', c2 = '{att_alternativa_c2}', d2 = '{att_alternativa_d2}', resposta2 = '{att_gabarito2}'
        WHERE id = {id};"""
        cursor.execute(comando)
        conexao.commit()

        return redirect('/pageadmin')
    else: # Caso o method for GET. GET é quando o usuário realiza apenas consulta (Query) no Banco de Dados
        return render_template('alterarprova.html', prova=prova)

# DELETAR
@app.route('/deletarprova/<int:id>') # Exclusão é realizado com a coleta do ID do cadastro
def deletarprova(id):
    comando = f'DELETE FROM prova WHERE id = {id};'
    cursor.execute(comando)
    conexao.commit()

    return redirect('/pageadmin') # Redirecionado para a Página Inicial

# # Função de coleta e tratamento de dados do formulário HTML CADASTRAR AVALIAÇÃO
# def coletar_dados():
#     global nome, data_nascimento, disciplina, hora, nota1, nota2, nota3, nota4, simulado, media # Indicando que essas variáveis são globais para ser utilizadas em qualquer função do código

#     # Coletando nome do formulário HTML
#     nome = request.form['nome']

#     # Formatando a data para Dia/Mês/Ano
#     data_nascimento = request.form['data_nascimento']
#     dia = data_nascimento[8:10]
#     mes = data_nascimento[5:7]
#     ano = data_nascimento[0:4]
#     data_nascimento = f'{dia}/{mes}/{ano}'

#     # Coletando a escola do formulário HTML
#     disciplina = request.form['disciplina']

#     # Coletando data atual do registro realizado
#     hora = datetime.today().strftime('%d/%m/%Y %H:%M:%S')

#     # Coleta das Notas
#     nota1 = tipo_float(request.form['nota1']) # Nota da Avaliação 1 (Peso 1.5)
#     nota2 = tipo_float(request.form['nota2']) # Nota da Avaliação 2 (Peso 1.5)
#     nota3 = tipo_float(request.form['nota3']) # Nota da Avaliação 3 (Peso 4)
#     nota4 = tipo_float(request.form['nota4']) # Nota da Avaliação 4 (Peso 3)
#     simulado = tipo_float(request.form['simulado']) # Nota do Simulado

#     # Trantando notas para tipo float
#     media = round(((((nota1*1.5) + (nota2*1.5) + (nota3*4) + (nota4*3)) / 10) + simulado),2) # Média das notas

# # Função para transformar para tipo Float
# def tipo_float(nota):
#     nota = nota.replace(',','.') # Números decimais no Python são com "." Ponto e não com vírgula ",", dessa forma é realizado a substituição da pontuação e transformado em tipo float

#     return float(nota)

# Linha de código padrão para execução
if __name__ == '__main__':
    app.run(debug=False)