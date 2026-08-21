package pe.com.upeu.PharmaBackend.exception;

public class RecursosNoEncontradoException extends RuntimeException {
    public RecursosNoEncontradoException(String mensaje) {
        super(mensaje);
    }
}
