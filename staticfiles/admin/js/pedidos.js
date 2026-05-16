(function () {
    if (!window.location.pathname.includes('/Cardapio/pedido/')) return;

    const INTERVALO_POLLING = 10000; // consulta o servidor a cada 10 segundos

    // Aplica cor de fundo na célula de status conforme o valor
    function aplicarCorStatus(celula, status) {
        celula.innerHTML = '';
        const span = document.createElement('span');
        span.textContent = status;

        if (status === 'Pago')        span.className = 'status-pago';
        if (status === 'Em Preparo')  span.className = 'status-preparo';
        if (status === 'Pronto')      span.className = 'status-pronto';

        celula.appendChild(span);
    }

    // Formata segundos em mm:ss para exibir no timer
    function formatarTempo(segundos) {
        const m = Math.floor(segundos / 60);
        const s = Math.floor(segundos % 60);
        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }

    const timers = {};

    function iniciarTimer(pedidoId, segundosRestantes) {
        if (timers[pedidoId]) clearInterval(timers[pedidoId]);

        let segundos = Math.floor(segundosRestantes);
        const celula = document.getElementById(`timer-${pedidoId}`);
        if (!celula) return;

        timers[pedidoId] = setInterval(function () {
            segundos--;
            if (segundos <= 0) {
                clearInterval(timers[pedidoId]);
                const linha = document.getElementById(`pedido-${pedidoId}`);
                if (linha) linha.remove();
                return;
            }
            celula.textContent = `⏱ ${formatarTempo(segundos)}`;
            if (segundos <= 60) celula.className = 'timer urgente';
        }, 1000);
    }

    function atualizarPedidos() {
        fetch('/admin/Cardapio/pedido/pedidos-ativos/')
            .then(res => res.json())
            .then(data => {
                const tabela = document.querySelector('#result_list tbody');
                if (!tabela) return;

                const idsAtivos = data.pedidos.map(p => p.id);

                tabela.querySelectorAll('tr[id^="pedido-"]').forEach(linha => {
                    const id = parseInt(linha.id.replace('pedido-', ''));
                    if (!idsAtivos.includes(id)) linha.remove();
                });

                data.pedidos.forEach(pedido => {
                    let linha = document.getElementById(`pedido-${pedido.id}`);

                    if (!linha) {
                        linha = document.createElement('tr');
                        linha.id = `pedido-${pedido.id}`;
                        linha.innerHTML = `
                            <td><a href="${pedido.url}">#${pedido.id}</a></td>
                            <td>Mesa ${pedido.mesa}</td>
                            <td class="celula-status"></td>
                            <td>${pedido.criado_em}</td>
                            <td class="celula-timer" id="timer-${pedido.id}"></td>
                        `;
                        tabela.appendChild(linha);
                    }

                    const celulaStatus = linha.querySelector('.celula-status');
                    aplicarCorStatus(celulaStatus, pedido.status);

                    if (pedido.segundos_restantes !== null) {
                        iniciarTimer(pedido.id, pedido.segundos_restantes);
                    }
                });
            });
    }

    atualizarPedidos();
    setInterval(atualizarPedidos, INTERVALO_POLLING);
})();