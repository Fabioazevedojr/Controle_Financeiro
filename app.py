import streamlit as st
from services.banco import (
    autenticar_usuario,
    listar_categorias,
    adicionar_categoria,
    excluir_categoria,
    atualizar_categoria,
    listar_lancamentos,
    adicionar_lancamento,
    excluir_lancamento,
    resumo_financeiro
)

st.set_page_config(page_title="Controle Financeiro", layout="centered")

# ==============================
# SESSÃO
# ==============================

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None


def logout():
    st.session_state["usuario"] = None
    st.rerun()


# ==============================
# LOGIN
# ==============================

def tela_login():
    st.title("🔐 Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar_usuario(email, senha)

        if user:
            st.session_state["usuario"] = {
                "id": user["id_usuario"],
                "nome": user["nome"],
                "admin": user["admin"]
            }
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Email ou senha inválidos.")


# ==============================
# TELA PRINCIPAL
# ==============================

def tela_principal():
    usuario = st.session_state["usuario"]

    st.title("💰 Controle Financeiro")
    st.write(f"Bem-vindo, **{usuario['nome']}**")

    if usuario["admin"]:
        st.success("Perfil: Administrador")
    else:
        st.info("Perfil: Usuário")

    st.divider()

    opcao = st.radio(
        "Selecione uma opção:",
        ["Dashboard", "Lançamentos", "Categorias", "Administração"]
    )

    # ==============================
    # ADMIN
    # ==============================
    if opcao == "Administração":
        if not usuario["admin"]:
            st.error("Acesso restrito ao administrador.")
            st.stop()

        st.subheader("Área Administrativa")
        st.write("Funções exclusivas do admin.")

    # ==============================
    # DASHBOARD
    # ==============================
    elif opcao == "Dashboard":
        st.subheader("Dashboard Financeiro")

        id_usuario = usuario["id"]

        col1, col2 = st.columns(2)
        data_inicio = col1.date_input("Data Inicial")
        data_fim = col2.date_input("Data Final")

        resumo = resumo_financeiro(
            id_usuario,
            data_inicio,
            data_fim
        )

        total_receita = resumo["Receita"]
        total_despesa = resumo["Despesa"]
        saldo = total_receita - total_despesa

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric("Receitas", f"R$ {total_receita:,.2f}")
        c2.metric("Despesas", f"R$ {total_despesa:,.2f}")
        c3.metric("Saldo", f"R$ {saldo:,.2f}")

        if saldo >= 0:
            st.success("Saldo positivo")
        else:
            st.error("Saldo negativo")

    # ==============================
    # LANÇAMENTOS
    # ==============================
    elif opcao == "Lançamentos":
        st.subheader("Gerenciar Lançamentos")

        id_usuario = usuario["id"]
        categorias = listar_categorias(id_usuario)

        if not categorias:
            st.warning("Cadastre uma categoria antes de lançar valores.")
            st.stop()

        with st.form("novo_lancamento"):
            data = st.date_input("Data")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            descricao = st.text_input("Descrição")

            categoria_dict = {
                f"{c['nome']} ({c['tipo']})": c["id_categoria"]
                for c in categorias
            }

            categoria_nome = st.selectbox(
                "Categoria",
                list(categoria_dict.keys())
            )

            submitted = st.form_submit_button("Adicionar")

            if submitted:
                adicionar_lancamento(
                    id_usuario,
                    categoria_dict[categoria_nome],
                    data,
                    valor,
                    descricao
                )
                st.success("Lançamento adicionado!")
                st.rerun()

        st.divider()

        lancamentos = listar_lancamentos(id_usuario)

        if lancamentos:
            for lanc in lancamentos:
                col1, col2, col3, col4, col5 = st.columns([2,2,2,3,1])

                col1.write(lanc["data"])
                col2.write(f"R$ {lanc['valor']:.2f}")
                col3.write(lanc["categoria"])
                col4.write(lanc["descricao"])

                if col5.button("X", key=f"del_l_{lanc['id_lancamento']}"):
                    excluir_lancamento(lanc["id_lancamento"])
                    st.rerun()
        else:
            st.info("Nenhum lançamento cadastrado.")

    # ==============================
    # CATEGORIAS
    # ==============================
    elif opcao == "Categorias":
        st.subheader("Gerenciar Categorias")

        id_usuario = usuario["id"]

        with st.form("nova_categoria"):
            nome = st.text_input("Nome da Categoria")
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])

            submitted = st.form_submit_button("Adicionar")

            if submitted:
                if nome.strip():
                    adicionar_categoria(nome, tipo, id_usuario)
                    st.success("Categoria adicionada!")
                    st.rerun()
                else:
                    st.warning("Informe o nome da categoria.")

        st.divider()

        categorias = listar_categorias(id_usuario)

        if categorias:
            for cat in categorias:
                col1, col2, col3 = st.columns([4,2,1])

                col1.write(cat["nome"])
                col2.write(cat["tipo"])

                if col3.button("Excluir", key=f"del_{cat['id_categoria']}"):
                    excluir_categoria(cat["id_categoria"])
                    st.rerun()
        else:
            st.info("Nenhuma categoria cadastrada.")

    st.divider()
    st.button("Sair", on_click=logout)


# ==============================
# CONTROLE GLOBAL
# ==============================

if st.session_state["usuario"] is None:
    tela_login()
else:
    tela_principal()