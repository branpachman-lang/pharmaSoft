package pe.com.upeu.PharmaBackend.service.generic;


public interface CrudService <REQ,RES,ID>{
    RES create(REQ t);
    RES update(ID id,REQ t);
    RES read(ID id);
    void delete(ID id);
    Iterable<RES> readAll();
}
