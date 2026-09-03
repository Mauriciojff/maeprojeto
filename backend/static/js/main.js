/* ============================================
   MAIN.JS — Interatividade global da Agenda da Mãe
   ============================================ */

// Auto-dismiss flash messages após 5 segundos
document.addEventListener('DOMContentLoaded', function () {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash, index) {
        setTimeout(function () {
            if (flash.parentNode) {
                flash.style.transition = 'opacity 0.5s';
                flash.style.opacity = '0';
                setTimeout(function () {
                    if (flash.parentNode) flash.parentNode.removeChild(flash);
                }, 500);
            }
        }, 5000 + (index * 100));
    });
});

// Máscara simples de telefone em inputs com data-telefone
document.addEventListener('input', function (e) {
    if (e.target && e.target.hasAttribute && e.target.hasAttribute('data-telefone')) {
        let valor = e.target.value.replace(/\D/g, '').slice(0, 11);
        if (valor.length > 10) {
            valor = valor.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
        } else if (valor.length > 6) {
            valor = valor.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
        } else if (valor.length > 2) {
            valor = valor.replace(/(\d{2})(\d{0,5})/, '($1) $2');
        }
        e.target.value = valor;
    }
});

// Confirmação genérica para formulários de exclusão
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (form && form.hasAttribute('data-confirmar')) {
        if (!confirm(form.getAttribute('data-confirmar'))) {
            e.preventDefault();
        }
    }
});
