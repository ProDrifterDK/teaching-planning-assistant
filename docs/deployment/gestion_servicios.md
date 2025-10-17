# Guía de Comandos para la Gestión de Servicios

Este documento describe los comandos útiles para administrar la API y el túnel de `ngrok` que se ejecutan como servicios de `systemd` en el sistema.

Todos los comandos deben ejecutarse con `sudo` ya que gestionan servicios del sistema.

## Comandos Generales

La mayoría de los comandos siguen la estructura: `sudo systemctl [accion] [nombre-del-servicio]`.

-   **Nombre del servicio de la API:** `teaching-assistant-api.service`
-   **Nombre del servicio de Ngrok:** `ngrok.service`

---

### Verificar el Estado de un Servicio

Para comprobar si un servicio está activo, si ha fallado o para ver un resumen de su estado reciente.

-   **Verificar la API:**
    ```bash
    sudo systemctl status teaching-assistant-api.service
    ```

-   **Verificar Ngrok:**
    ```bash
    sudo systemctl status ngrok.service
    ```

---

### Reiniciar Servicios

Este comando es útil cuando has hecho cambios en el código de la API y necesitas aplicar las actualizaciones. Reiniciar el servicio de la API detendrá el proceso actual y lo iniciará de nuevo.

-   **Reiniciar solo la API:**
    ```bash
    sudo systemctl restart teaching-assistant-api.service
    ```

-   **Reiniciar solo Ngrok:**
    ```bash
    sudo systemctl restart ngrok.service
    ```

-   **Reiniciar ambos servicios a la vez:**
    Puedes encadenar los comandos para reiniciar ambos.
    ```bash
    sudo systemctl restart teaching-assistant-api.service && sudo systemctl restart ngrok.service
    ```

---

### Ver Logs

Los logs son esenciales para depurar problemas o ver la actividad de los servicios (por ejemplo, las peticiones que llegan a la API).

-   **Ver los últimos 50 logs de la API:**
    ```bash
    sudo journalctl -u teaching-assistant-api.service -n 50 --no-pager
    ```

-   **Ver los logs de la API en tiempo real (como `tail -f`):**
    Útil para ver la actividad en vivo. Presiona `Ctrl+C` para salir.
    ```bash
    sudo journalctl -u teaching-assistant-api.service -f
    ```

---

### Obtener la URL del Túnel de Ngrok

Dado que `ngrok` se ejecuta en segundo plano, no verás la URL en tu terminal. Para obtenerla, puedes consultar la API local que `ngrok` proporciona.

-   **Obtener la URL pública:**
    ```bash
    curl -s http://localhost:4040/api/tunnels | jq -r .tunnels[0].public_url
    ```
    *(Nota: Requiere tener `jq` instalado para obtener solo la URL. Si no lo tienes, el mismo comando sin `| jq ...` te mostrará toda la información en formato JSON).*
