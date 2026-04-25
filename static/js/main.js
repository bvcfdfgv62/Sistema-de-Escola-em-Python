document.addEventListener('DOMContentLoaded', () => {
    // Configurações e Elementos
    const views = {
        dashboard: document.getElementById('viewDashboard'),
        alunos: document.getElementById('viewAlunos')
    };
    
    const modals = {
        add: document.getElementById('modalAdd'),
        nota: document.getElementById('modalNota')
    };

    let currentAlunoId = null;

    // --- CARREGAMENTO DE DADOS ---
    const loadAll = async () => {
        await Promise.all([loadStats(), loadAlunos()]);
    };

    const loadStats = async () => {
        const res = await fetch('/stats');
        const data = await res.json();
        document.getElementById('statTotal').textContent = data.total;
        document.getElementById('statMedia').textContent = data.media_geral.toFixed(1);
        document.getElementById('statAprovados').textContent = data.aprovados;
    };

    const loadAlunos = async () => {
        const res = await fetch('/alunos/list');
        const data = await res.json();
        renderTable(data, document.getElementById('recentList'));
        renderTable(data, document.getElementById('fullList'));
    };

    const renderTable = (data, container) => {
        if (!container) return;
        container.innerHTML = '';
        
        if (data.length === 0) {
            container.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--text-dim);">Nenhum aluno cadastrado.</div>';
            return;
        }

        data.forEach(aluno => {
            const badgeClass = aluno.status === 'APROVADO' ? 'badge-success' : (aluno.status === 'RECUPERAÇÃO' ? 'badge-neutral' : 'badge-error');
            
            const row = document.createElement('div');
            row.className = 'table-row';
            row.innerHTML = `
                <div class="table-col table-col-name">${aluno.nome}</div>
                <div class="table-col">${aluno.qtd_notas} notas</div>
                <div class="table-col"><strong>${aluno.media.toFixed(1)}</strong></div>
                <div class="table-col">
                    <span class="badge ${badgeClass}">${aluno.status}</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-ghost btn-add-nota" style="padding: 4px 8px;">✏️</button>
                    <button class="btn-ghost btn-del-aluno" style="padding: 4px 8px;">🗑️</button>
                </div>
            `;

            row.querySelector('.btn-add-nota').onclick = () => openNotaModal(aluno.id, aluno.nome);
            row.querySelector('.btn-del-aluno').onclick = () => deleteAluno(aluno.id);
            
            container.appendChild(row);
        });
    };

    // --- AÇÕES ---
    const openNotaModal = (id, nome) => {
        currentAlunoId = id;
        document.getElementById('notaTargetNome').textContent = `Para: ${nome}`;
        modals.nota.classList.add('active');
    };

    const deleteAluno = async (id) => {
        if (confirm('Deseja remover este aluno permanentemente?')) {
            await fetch('/alunos/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            loadAll();
        }
    };

    document.getElementById('btnSaveAluno').onclick = async () => {
        const nome = document.getElementById('inputNome').value;
        if (!nome) return;
        
        const res = await fetch('/alunos/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome })
        });
        const result = await res.json();
        
        if (result.success) {
            modals.add.classList.remove('active');
            document.getElementById('inputNome').value = '';
            loadAll();
        } else {
            alert(result.message);
        }
    };

    document.getElementById('btnSaveNota').onclick = async () => {
        const nota = document.getElementById('inputNota').value;
        if (!nota) return;

        const res = await fetch('/alunos/add_nota', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: currentAlunoId, nota })
        });
        
        modals.nota.classList.remove('active');
        document.getElementById('inputNota').value = '';
        loadAll();
    };

    // --- NAVEGAÇÃO E UI ---
    document.querySelectorAll('.menu-item').forEach(btn => {
        btn.onclick = () => {
            const view = btn.getAttribute('data-view');
            document.querySelectorAll('.menu-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            Object.keys(views).forEach(v => views[v].style.display = 'none');
            views[view].style.display = 'block';
            document.getElementById('pageTitle').textContent = view.charAt(0).toUpperCase() + view.slice(1);
        };
    });

    document.getElementById('btnAddAluno').onclick = () => modals.add.classList.add('active');
    document.getElementById('btnCloseAdd').onclick = () => modals.add.classList.remove('active');
    document.getElementById('btnCloseNota').onclick = () => modals.nota.classList.remove('active');

    loadAll();
});
