(function () {
    if (!window.location.pathname.includes('/Cardapio/pedido/')) return;

    const INTERVALO_POLLING = 10000;
    const timers = {};

    function formatarTempo(segundos) {
        const m = Math.floor(segundos / 60);
        const s = Math.floor(segundos % 60);
        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }

    function badgeStatus(status) {
        const mapa = {
            'Aguardando Pagamento': '<span class="status-aguardando">⏳ Aguardando Pagamento</span>',
            'Pago':                 '<span class="status-pago">💰 Pago</span>',
            'Em Preparo':           '<span class="status-preparo">👨‍🍳 Em Preparo</span>',
            'Pronto':               '<span class="status-pronto">✅ Pronto</span>',
        };
        return mapa[status] || status;
    }

    function montarProximaAcao(pedido) {
        if (pedido.status === 'Aguardando Pagamento') {
            return '<span class="acao-texto">Aguardando pagamento do cliente</span>';
        }
        if (pedido.status === 'Pronto') {
            return `<span class="acao-texto acao-pronto">🍽️ Entregar na mesa ${pedido.mesa}</span>`;
        }
        return `<a href="${pedido.url}" class="button acao-btn">${pedido.proxima_acao}</a>`;
    }

    function atualizarContador() {
        const total = document.querySelectorAll('#result_list tbody tr[data-pedido-id]').length;
        const rodape = document.querySelector('#changelist-form p');
        if (rodape) {
            rodape.textContent = total === 1 ? '1 pedido' : `${total} pedidos`;
        }
    }

    function iniciarTimer(pedidoId, segundosRestantes) {
        if (timers[pedidoId]) clearInterval(timers[pedidoId]);

        let segundos = Math.floor(segundosRestantes);

        timers[pedidoId] = setInterval(function () {
            segundos--;
            const celula = document.getElementById(`timer-${pedidoId}`);

            if (!celula) {
                clearInterval(timers[pedidoId]);
                return;
            }

            if (segundos <= 0) {
                clearInterval(timers[pedidoId]);
                celula.textContent = '';
                celula.className = '';
                return;
            }

            celula.textContent = `⏱ ${formatarTempo(segundos)}`;
            celula.className = '';
            if (segundos <= 60) {
                celula.className = 'timer urgente';
            } else {
                celula.className = 'timer';
            }
        }, 1000);
    }

    function atualizarPedidos() {
        fetch('/admin/Cardapio/pedido/pedidos-ativos/')
            .then(res => res.json())
            .then(data => {
                const tabela = document.querySelector('#result_list tbody');
                if (!tabela) return;

                const idsNovos = data.pedidos.map(p => String(p.id));

                tabela.querySelectorAll('tr[data-pedido-id]').forEach(linha => {
                    const id = linha.getAttribute('data-pedido-id');
                    if (!idsNovos.includes(id)) linha.remove();
                });

                data.pedidos.forEach(pedido => {
                    let linha = tabela.querySelector(`tr[data-pedido-id="${pedido.id}"]`);

                    if (!linha) {
                        linha = document.createElement('tr');
                        linha.setAttribute('data-pedido-id', String(pedido.id));
                        linha.innerHTML = `
                            <td><a href="${pedido.url}">#${pedido.id}</a></td>
                            <td>Mesa ${pedido.mesa}</td>
                            <td>${pedido.restaurante}</td>
                            <td class="celula-status"></td>
                            <td>${pedido.criado_em}</td>
                            <td class="celula-timer" id="timer-${pedido.id}"></td>
                            <td class="celula-acao"></td>
                        `;
                        tabela.appendChild(linha);
                    }

                    linha.querySelector('.celula-status').innerHTML = badgeStatus(pedido.status);
                    linha.querySelector('.celula-acao').innerHTML = montarProximaAcao(pedido);

                    if (pedido.segundos_restantes !== null && !timers[pedido.id]) {
                        const celulaTimer = document.getElementById(`timer-${pedido.id}`);
                        if (celulaTimer) {
                            celulaTimer.textContent = `⏱ ${formatarTempo(Math.floor(pedido.segundos_restantes))}`;
                            celulaTimer.className = 'timer';
                        }
                        iniciarTimer(pedido.id, pedido.segundos_restantes);
                    }
                });

                atualizarContador();
            });
    }

    atualizarPedidos();
    setInterval(atualizarPedidos, INTERVALO_POLLING);
})();