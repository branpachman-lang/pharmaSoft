package pe.com.upeu.PharmaBackend.service.impl;

import org.springframework.stereotype.Service;
import pe.com.upeu.PharmaBackend.entity.Categoria;
import pe.com.upeu.PharmaBackend.repository.CategoriaRepository;
import pe.com.upeu.PharmaBackend.service.service.CategoriaService;

import java.util.Optional;
@Service
public class CategoriaServiceImpl implements CategoriaService {
    private final CategoriaRepository categoriaRepository;
    public CategoriaServiceImpl(CategoriaRepository categoriaRepository) {
        this.categoriaRepository = categoriaRepository;
    }
    @Override
    public Categoria create(Categoria categoria) {
        return categoriaRepository.save(categoria);
    }

    @Override
    public Categoria update(Categoria categoria) {
        return categoriaRepository.save(categoria);
    }

    @Override
    public Optional<Categoria> read(Long aLong) {
        return categoriaRepository.findById(aLong);
    }

    @Override
    public void delete(Long aLong) {
        categoriaRepository.deleteById(aLong);
    }

    @Override
    public Iterable<Categoria> readAll() {
        return categoriaRepository.findAll();
    }
}
