// PreAtende — pequenos aprimoramentos de interface (sem dependências externas)
document.addEventListener("DOMContentLoaded", function () {
    // Confirmação ao cancelar um pré-atendimento na fila
    var selectStatus = document.querySelector('select[name="status"]');
    var formStatus = selectStatus ? selectStatus.closest("form") : null;

    if (formStatus) {
        formStatus.addEventListener("submit", function (evento) {
            if (selectStatus.value === "cancelado") {
                var confirmado = window.confirm("Tem certeza que deseja cancelar este pré-atendimento?");
                if (!confirmado) {
                    evento.preventDefault();
                }
            }
        });
    }

    // Fecha mensagens de alerta (flash) automaticamente após alguns segundos
    document.querySelectorAll(".flash").forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity 0.4s ease";
            el.style.opacity = "0";
        }, 6000);
    });
});
