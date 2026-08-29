package pe.com.upeu.PharmaBackend.dto;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import pe.com.upeu.PharmaBackend.entity.Categoria;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class ProductoDTO {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(length = 50, nullable = false)
    @NotBlank(message = "El espacio del nombre no debe estar vacio")
    private String nombre;

    @Column(nullable = false)
    @NotBlank(message = "El espacio del precio debe tener un valor")
    private BigDecimal precio;

    @Column(nullable = false)
    private int stock;


    @Column(nullable = false)
    private Boolean estado;


    @Column(name = "fecha_creacion",nullable = false, updatable = false)
    private LocalDateTime fechaCreacion;

    @Column(name = "fecha_modificacion")
    private LocalDateTime fechaModificacion;

    @PrePersist
    public void prePersist() {
        this.fechaCreacion = LocalDateTime.now();
        if(estado==null){
            estado=true;
        }
    }
    @PreUpdate
    public void preUpdate() {
        this.fechaModificacion = LocalDateTime.now();
    }

    @NotNull
    @ManyToOne
    @JoinColumn(name="categoria_id")
    private Categoria categoria;
}