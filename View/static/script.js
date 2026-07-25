const API_BASE = window.location.protocol === "file:"
    ? "http://127.0.0.1:5000"
    : window.location.origin;

const state = {
    setores: [],
    brigadistas: [],
    extintores: [],
    inspecoes: [],
    notificacoes: []
};

const titles = {
    dashboard: {
        title: "Dashboard",
        subtitle: "Painel principal"
    },
    setores: {
        title: "Setores",
        subtitle: "Setores"
    },
    brigadistas: {
        title: "Brigadistas",
        subtitle: "Equipe"
    },
    extintores: {
        title: "Extintores",
        subtitle: "Equipamentos"
    },
    inspecoes: {
        title: "Inspeções",
        subtitle: "Inspeções"
    },
    notificacoes: {
        title: "Notificações",
        subtitle: "Alertas"
    }
};

document.addEventListener("DOMContentLoaded", () => {
    configurarMenu();
    configurarForms();
    configurarBotoes();
    carregarTudo();
});

function configurarMenu() {
    document.querySelectorAll('[data-bs-toggle="pill"]').forEach((btn) => {
        btn.addEventListener("shown.bs.tab", (event) => {
            const view = event.target.dataset.view;
            atualizarTitulo(view);
        });
    });

    document.querySelectorAll("[data-open-tab]").forEach((btn) => {
        btn.addEventListener("click", () => abrirAba(btn.dataset.openTab));
    });
}

function abrirAba(view) {
    const btn = document.querySelector(`[data-view="${view}"]`);
    if (!btn || !window.bootstrap) return;
    const tab = new bootstrap.Tab(btn);
    tab.show();
}

function atualizarTitulo(view) {
    const data = titles[view] || titles.dashboard;
    document.getElementById("view-title").textContent = data.title;
    document.getElementById("view-subtitle").textContent = data.subtitle;
}

function configurarBotoes() {
    document.getElementById("btn-refresh").addEventListener("click", carregarTudo);
    document.getElementById("btn-verificar-vencimentos").addEventListener("click", verificarVencimentos);

    document.querySelectorAll("[data-reset]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form = document.getElementById(btn.dataset.reset);
            limparForm(form);
        });
    });
}

function configurarForms() {
    document.getElementById("form-setor").addEventListener("submit", salvarSetor);
    document.getElementById("form-brigadista").addEventListener("submit", salvarBrigadista);
    document.getElementById("form-extintor").addEventListener("submit", salvarExtintor);
    document.getElementById("form-inspecao").addEventListener("submit", salvarInspecao);
}

async function api(endpoint, options = {}) {
    const config = {
        headers: {
            "Content-Type": "application/json"
        },
        ...options
    };

    const response = await fetch(`${API_BASE}${endpoint}`, config);
    let data = null;

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        const mensagem = data.erro || data.mensagem || data.detalhes || "Erro na requisição";
        throw new Error(mensagem);
    }

    return data;
}

function formToObject(form) {
    const data = new FormData(form);
    const obj = Object.fromEntries(data.entries());

    form.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
        obj[checkbox.name] = checkbox.checked;
    });

    Object.keys(obj).forEach((key) => {
        if (obj[key] === "") {
            obj[key] = null;
        }
    });

    return obj;
}

function limparForm(form) {
    form.reset();
    form.querySelectorAll("input[type='hidden']").forEach((input) => input.value = "");
    form.querySelectorAll("input:disabled").forEach((input) => input.disabled = false);

    const titulo = form.querySelector("h3");
    if (titulo) {
        titulo.textContent = titulo.textContent.replace("Editar", "Cadastrar");
    }
}

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4500);
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatDate(value) {
    if (!value) return "-";

    const dateOnly = String(value).split("T")[0].split(" ")[0];

    if (/^\d{4}-\d{2}-\d{2}$/.test(dateOnly)) {
        const [year, month, day] = dateOnly.split("-");
        return `${day}/${month}/${year}`;
    }

    return String(value).replace("T", " ");
}

function formatDateTimeForInput(value) {
    if (!value) return "";
    return String(value).replace(" ", "T").slice(0, 16);
}

function badgeStatus(status) {
    const valor = status || "-";
    let classe = "badge-soft-success";

    if (["Vencido", "Condenado"].includes(valor)) {
        classe = "badge-soft-danger";
    } else if (["Em manutenção", "Reserva"].includes(valor)) {
        classe = "badge-soft-warning";
    } else if (valor === "Enviado") {
        classe = "badge-soft-info";
    }

    return `<span class="badge rounded-pill ${classe}">${escapeHtml(valor)}</span>`;
}

function emptyRow(colspan, text = "Nenhum registro encontrado.") {
    return `<tr><td class="empty-row" colspan="${colspan}">${escapeHtml(text)}</td></tr>`;
}

async function carregarTudo() {
    await verificarApi();

    try {
        await carregarSetores();
        await carregarBrigadistas();
        await carregarExtintores();
        preencherSelects();
        await carregarInspecoes();
        await carregarNotificacoes();
        await carregarDashboard();
        showToast("Dados atualizados.");
    } catch (error) {
        showToast(error.message);
    }
}

async function verificarApi() {
    const dot = document.getElementById("api-dot");
    const text = document.getElementById("api-status-text");

    try {
        await api("/api/health");
        dot.className = "api-dot online";
        text.textContent = "Sistema online";
    } catch {
        dot.className = "api-dot offline";
        text.textContent = "Sem conexão";
    }
}

async function carregarDashboard() {
    try {
        const dados = await api("/api/dashboard");

        document.getElementById("card-setores").textContent = dados.total_setores ?? 0;
        document.getElementById("card-brigadistas").textContent = dados.total_brigadistas ?? 0;
        document.getElementById("card-extintores").textContent = dados.total_extintores ?? 0;
        document.getElementById("card-inspecoes").textContent = dados.total_inspecoes ?? 0;
        document.getElementById("card-vencidos").textContent = dados.extintores_vencidos ?? 0;
        document.getElementById("card-vencendo").textContent = dados.extintores_vencendo_30_dias ?? 0;

        renderDashboardInspecoes(dados.ultimas_inspecoes || []);
        renderDashboardVencimentos(dados.proximos_vencimentos || []);
        renderBars("dashboard-status-bars", dados.status_extintores || [], "extintor_status", "total", "status");
        renderBars("dashboard-agent-bars", dados.agentes_extintores || [], "tipo_agente", "total", "agent");
    } catch {
        document.getElementById("dashboard-inspecoes").innerHTML = emptyRow(6, "Nenhum registro encontrado.");
        document.getElementById("dashboard-vencimentos").innerHTML = emptyRow(6, "Sem vencimentos próximos.");
        renderBars("dashboard-status-bars", [], "extintor_status", "total", "status");
        renderBars("dashboard-agent-bars", [], "tipo_agente", "total", "agent");
    }
}

function renderDashboardInspecoes(lista) {
    const tbody = document.getElementById("dashboard-inspecoes");
    tbody.innerHTML = lista.length
        ? lista.map(item => `
            <tr>
                <td>${escapeHtml(item.id_inspecao)}</td>
                <td><strong>${escapeHtml(item.numero_patrimonio)}</strong></td>
                <td>${escapeHtml(item.nome_brigadista)}</td>
                <td>${escapeHtml(item.tipo_agente)}</td>
                <td>${formatDate(item.data_inspecao)}</td>
                <td>${formatDate(item.data_vencimento_nivel1)}</td>
            </tr>
        `).join("")
        : emptyRow(6);
}

function renderDashboardVencimentos(lista) {
    const tbody = document.getElementById("dashboard-vencimentos");
    tbody.innerHTML = lista.length
        ? lista.map(item => {
            const dias = Number(item.dias_restantes);
            const diasTexto = dias < 0 ? `${Math.abs(dias)} dia(s) vencido` : `${dias} dia(s)`;
            return `
                <tr>
                    <td><strong>${escapeHtml(item.numero_patrimonio)}</strong></td>
                    <td>${escapeHtml(item.tipo_agente)}</td>
                    <td>${escapeHtml(item.nome_setor)}</td>
                    <td>${formatDate(item.validade_carga)}</td>
                    <td>${escapeHtml(diasTexto)}</td>
                    <td>${badgeStatus(item.extintor_status)}</td>
                </tr>
            `;
        }).join("")
        : emptyRow(6, "Sem extintores vencendo nos próximos 60 dias.");
}

function renderBars(containerId, lista, labelKey, valueKey, type) {
    const container = document.getElementById(containerId);
    const total = lista.reduce((acc, item) => acc + Number(item[valueKey] || 0), 0);

    if (!lista.length || total === 0) {
        container.innerHTML = `<p class="text-muted m-0">Sem dados para exibir.</p>`;
        return;
    }

    container.innerHTML = lista.map((item) => {
        const valor = Number(item[valueKey] || 0);
        const percent = Math.max(4, Math.round((valor / total) * 100));
        const classe = type === "agent" ? "progress-bar agent" : "progress-bar";
        return `
            <div class="chart-line">
                <div class="chart-line-top">
                    <span>${escapeHtml(item[labelKey])}</span>
                    <strong>${valor}</strong>
                </div>
                <div class="progress" role="progressbar" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100">
                    <div class="${classe}" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    }).join("");
}

async function carregarSetores() {
    state.setores = await api("/api/setores");
    renderSetores();
}

function renderSetores() {
    const tbody = document.getElementById("tabela-setores");

    tbody.innerHTML = state.setores.length
        ? state.setores.map(setor => `
            <tr>
                <td>${escapeHtml(setor.id_setor)}</td>
                <td><strong>${escapeHtml(setor.nome_setor)}</strong></td>
                <td>${escapeHtml(setor.bloco_pavimento)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="editarSetor(${setor.id_setor})">Editar</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deletarRegistro('/api/setores/${setor.id_setor}', carregarTudo)">Excluir</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : emptyRow(4);
}

async function salvarSetor(event) {
    event.preventDefault();

    const form = event.target;
    const dados = formToObject(form);
    const id = dados.id_setor;
    delete dados.id_setor;

    try {
        if (id) {
            await api(`/api/setores/${id}`, {
                method: "PUT",
                body: JSON.stringify(dados)
            });
            showToast("Setor atualizado.");
        } else {
            await api("/api/setores", {
                method: "POST",
                body: JSON.stringify(dados)
            });
            showToast("Setor cadastrado.");
        }

        limparForm(form);
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

function editarSetor(id) {
    const setor = state.setores.find(item => item.id_setor === id);
    if (!setor) return;

    const form = document.getElementById("form-setor");
    form.id_setor.value = setor.id_setor;
    form.nome_setor.value = setor.nome_setor;
    form.bloco_pavimento.value = setor.bloco_pavimento;
    form.querySelector("h3").textContent = "Editar setor";
    abrirAba("setores");
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function carregarBrigadistas() {
    state.brigadistas = await api("/api/brigadistas");
    renderBrigadistas();
}

function renderBrigadistas() {
    const tbody = document.getElementById("tabela-brigadistas");

    tbody.innerHTML = state.brigadistas.length
        ? state.brigadistas.map(item => `
            <tr>
                <td>${escapeHtml(item.id_brigadista)}</td>
                <td><strong>${escapeHtml(item.nome_brigadista)}</strong></td>
                <td>${escapeHtml(item.cpf)}</td>
                <td>${escapeHtml(item.telefone)}</td>
                <td>${escapeHtml(item.nome_setor || "-")}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="editarBrigadista(${item.id_brigadista})">Editar</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deletarRegistro('/api/brigadistas/${item.id_brigadista}', carregarTudo)">Excluir</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : emptyRow(6);
}

async function salvarBrigadista(event) {
    event.preventDefault();

    const form = event.target;
    const dados = formToObject(form);
    const id = dados.id_brigadista;
    dados.id_setor = Number(dados.id_setor);
    delete dados.id_brigadista;

    try {
        if (id) {
            await api(`/api/brigadistas/${id}`, {
                method: "PUT",
                body: JSON.stringify(dados)
            });
            showToast("Brigadista atualizado.");
        } else {
            await api("/api/brigadistas", {
                method: "POST",
                body: JSON.stringify(dados)
            });
            showToast("Brigadista cadastrado.");
        }

        limparForm(form);
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

function editarBrigadista(id) {
    const item = state.brigadistas.find(registro => registro.id_brigadista === id);
    if (!item) return;

    const form = document.getElementById("form-brigadista");
    form.id_brigadista.value = item.id_brigadista;
    form.nome_brigadista.value = item.nome_brigadista || "";
    form.cpf.value = item.cpf || "";
    form.telefone.value = item.telefone || "";
    form.whatsapp.value = item.whatsapp || "";
    form.email.value = item.email || "";
    form.data_treinamento.value = item.data_treinamento || "";
    form.id_setor.value = item.id_setor || "";
    form.querySelector("h3").textContent = "Editar brigadista";
    abrirAba("brigadistas");
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function carregarExtintores() {
    state.extintores = await api("/api/extintores");
    renderExtintores();
}

function renderExtintores() {
    const tbody = document.getElementById("tabela-extintores");

    tbody.innerHTML = state.extintores.length
        ? state.extintores.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.numero_patrimonio)}</strong></td>
                <td>${escapeHtml(item.tipo_agente)}</td>
                <td>${escapeHtml(item.classe_incendio)}</td>
                <td>${escapeHtml(item.nome_setor || "-")}</td>
                <td>${formatDate(item.validade_carga)}</td>
                <td>${badgeStatus(item.extintor_status)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="editarExtintor('${encodeURIComponent(item.numero_patrimonio)}')">Editar</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deletarRegistro('/api/extintores/${encodeURIComponent(item.numero_patrimonio)}', carregarTudo)">Excluir</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : emptyRow(7);
}

async function salvarExtintor(event) {
    event.preventDefault();

    const form = event.target;
    const dados = formToObject(form);
    const editId = dados.edit_numero_patrimonio;

    dados.id_setor = Number(dados.id_setor);
    delete dados.edit_numero_patrimonio;

    try {
        if (editId) {
            await api(`/api/extintores/${encodeURIComponent(editId)}`, {
                method: "PUT",
                body: JSON.stringify(dados)
            });
            showToast("Extintor atualizado.");
        } else {
            await api("/api/extintores", {
                method: "POST",
                body: JSON.stringify(dados)
            });
            showToast("Extintor cadastrado.");
        }

        limparForm(form);
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

function editarExtintor(encodedPatrimonio) {
    const patrimonio = decodeURIComponent(encodedPatrimonio);
    const item = state.extintores.find(registro => registro.numero_patrimonio === patrimonio);
    if (!item) return;

    const form = document.getElementById("form-extintor");
    form.edit_numero_patrimonio.value = item.numero_patrimonio;
    form.numero_patrimonio.value = item.numero_patrimonio;
    form.numero_patrimonio.disabled = true;
    form.id_setor.value = item.id_setor || "";
    form.codigo_lacre.value = item.codigo_lacre || "";
    form.tipo_agente.value = item.tipo_agente || "PQS";
    form.classe_incendio.value = item.classe_incendio || "ABC";
    form.localizacao_detalhada.value = item.localizacao_detalhada || "";
    form.validade_carga.value = item.validade_carga || "";
    form.data_aquisicao.value = item.data_aquisicao || "";
    form.data_ultima_recarga.value = item.data_ultima_recarga || "";
    form.extintor_status.value = item.extintor_status || "Disponível";
    form.querySelector("h3").textContent = "Editar extintor";
    abrirAba("extintores");
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function carregarInspecoes() {
    state.inspecoes = await api("/api/inspecoes");
    renderInspecoes();
}

function renderInspecoes() {
    const tbody = document.getElementById("tabela-inspecoes");

    tbody.innerHTML = state.inspecoes.length
        ? state.inspecoes.map(item => `
            <tr>
                <td>${escapeHtml(item.id_inspecao)}</td>
                <td><strong>${escapeHtml(item.numero_patrimonio)}</strong></td>
                <td>${escapeHtml(item.nome_brigadista || "-")}</td>
                <td>${formatDate(item.data_inspecao)}</td>
                <td>${escapeHtml(item.status_manometro)}</td>
                <td>${formatDate(item.data_vencimento_nivel1)}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="editarInspecao(${item.id_inspecao})">Editar</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deletarRegistro('/api/inspecoes/${item.id_inspecao}', carregarTudo)">Excluir</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : emptyRow(7);
}

async function salvarInspecao(event) {
    event.preventDefault();

    const form = event.target;
    const dados = formToObject(form);
    const id = dados.id_inspecao;
    dados.id_brigadista = Number(dados.id_brigadista);
    delete dados.id_inspecao;

    try {
        if (id) {
            await api(`/api/inspecoes/${id}`, {
                method: "PUT",
                body: JSON.stringify(dados)
            });
            showToast("Inspeção atualizada.");
        } else {
            await api("/api/inspecoes", {
                method: "POST",
                body: JSON.stringify(dados)
            });
            showToast("Inspeção cadastrada.");
        }

        limparForm(form);
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

function editarInspecao(id) {
    const item = state.inspecoes.find(registro => registro.id_inspecao === id);
    if (!item) return;

    const form = document.getElementById("form-inspecao");
    form.id_inspecao.value = item.id_inspecao;
    form.id_brigadista.value = item.id_brigadista || "";
    form.numero_patrimonio.value = item.numero_patrimonio || "";
    form.data_inspecao.value = formatDateTimeForInput(item.data_inspecao);
    form.status_manometro.value = item.status_manometro || "Pressão Padrão";
    form.status_carga.value = item.status_carga || "Cheio";
    form.status_agente_disparo.value = item.status_agente_disparo || "Conforme";
    form.lacre_rompido.checked = Boolean(item.lacre_rompido);
    form.data_teste_nivel1.value = item.data_teste_nivel1 || "";
    form.data_teste_nivel2.value = item.data_teste_nivel2 || "";
    form.data_teste_nivel3.value = item.data_teste_nivel3 || "";
    form.integridade_visual.value = item.integridade_visual || "Excelente";
    form.arquivo_evidencia_imagem_path.value = item.arquivo_evidencia_imagem_path || "";
    form.querySelector("h3").textContent = "Editar inspeção";
    abrirAba("inspecoes");
    form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function carregarNotificacoes() {
    state.notificacoes = await api("/api/notificacoes");
    renderNotificacoes();
}

function renderNotificacoes() {
    const tbody = document.getElementById("tabela-notificacoes");

    tbody.innerHTML = state.notificacoes.length
        ? state.notificacoes.map(item => `
            <tr>
                <td>${escapeHtml(item.id_notificacao)}</td>
                <td><strong>${escapeHtml(item.numero_patrimonio)}</strong></td>
                <td>${escapeHtml(item.nome_brigadista || "-")}</td>
                <td>${escapeHtml(item.dias_para_vencimento)} dia(s)</td>
                <td>${item.enviado ? badgeStatus("Enviado") : badgeStatus("Pendente")}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-outline-success" onclick="enviarNotificacao(${item.id_notificacao})" ${item.enviado ? "disabled" : ""}>Enviar</button>
                        <button class="btn btn-sm btn-outline-primary" onclick="marcarEnviada(${item.id_notificacao})" ${item.enviado ? "disabled" : ""}>Marcar enviada</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : emptyRow(6);
}

async function verificarVencimentos() {
    const dias = Number(document.getElementById("dias-alerta").value || 30);

    try {
        const resposta = await api("/api/notificar/verificar", {
            method: "POST",
            body: JSON.stringify({ dias_alerta: dias })
        });

        showToast(resposta.mensagem || "Verificação concluída.");
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

async function enviarNotificacao(id) {
    try {
        const resposta = await api(`/api/notificacoes/${id}/enviar`, { method: "POST" });
        showToast(resposta.mensagem || "Notificação enviada.");
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

async function marcarEnviada(id) {
    try {
        const resposta = await api(`/api/notificacoes/${id}/marcar-enviada`, { method: "PUT" });
        showToast(resposta.mensagem || "Notificação marcada como enviada.");
        await carregarTudo();
    } catch (error) {
        showToast(error.message);
    }
}

async function deletarRegistro(endpoint, callback) {
    if (!confirm("Deseja realmente excluir este registro?")) return;

    try {
        await api(endpoint, { method: "DELETE" });
        showToast("Registro excluído.");
        await callback();
    } catch (error) {
        showToast(error.message);
    }
}

function preencherSelects() {
    document.querySelectorAll("select[data-select='setores']").forEach((select) => {
        const valorAtual = select.value;
        select.innerHTML = `<option value="">Selecione um setor</option>` + state.setores.map(setor => `
            <option value="${setor.id_setor}">${escapeHtml(setor.nome_setor)} - ${escapeHtml(setor.bloco_pavimento)}</option>
        `).join("");
        select.value = valorAtual;
    });

    document.querySelectorAll("select[data-select='brigadistas']").forEach((select) => {
        const valorAtual = select.value;
        select.innerHTML = `<option value="">Selecione um brigadista</option>` + state.brigadistas.map(item => `
            <option value="${item.id_brigadista}">${escapeHtml(item.nome_brigadista)}</option>
        `).join("");
        select.value = valorAtual;
    });

    document.querySelectorAll("select[data-select='extintores']").forEach((select) => {
        const valorAtual = select.value;
        select.innerHTML = `<option value="">Selecione um extintor</option>` + state.extintores.map(item => `
            <option value="${escapeHtml(item.numero_patrimonio)}">${escapeHtml(item.numero_patrimonio)} - ${escapeHtml(item.tipo_agente)}</option>
        `).join("");
        select.value = valorAtual;
    });
}
