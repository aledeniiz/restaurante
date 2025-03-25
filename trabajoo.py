import threading
import queue
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

# Configuración del sistema
NUM_CLIENTES = 5
NUM_COCINEROS = 3
MAX_PEDIDOS_POR_CLIENTE = 3
MAX_PLATOS_POR_PEDIDO = 4
MAX_COLA_PEDIDOS = 10

class Prioridad(IntEnum):
    ALTA = 1
    MEDIA = 2
    BAJA = 3

@dataclass(order=True)
class Plato:
    prioridad: Prioridad = field(compare=True)
    tiempo_coccion: float = field(compare=False)
    nombre: str = field(compare=False)
    cliente_id: int = field(compare=False)
    pedido_id: int = field(compare=False)
    inicio_preparacion: datetime = field(default=None, compare=False)
    fin_preparacion: datetime = field(default=None, compare=False)

class Restaurante:
    def __init__(self):
        self.cola_pedidos = queue.PriorityQueue(maxsize=MAX_COLA_PEDIDOS)
        self.lock = threading.Lock()
        self.evento_cierre = threading.Event()
        self.cocineros = []
        self.clientes = []

    def iniciar_simulacion(self):
        print("🍽️  SIMULACIÓN DE RESTAURANTE CONCURRENTE 🍽️\n")
        
        # Crear cocineros
        for i in range(NUM_COCINEROS):
            cocinero = threading.Thread(
                target=self._trabajar_cocinero,
                args=(i+1,),
                daemon=True
            )
            self.cocineros.append(cocinero)
            cocinero.start()

        # Crear clientes
        for i in range(NUM_CLIENTES):
            cliente = threading.Thread(
                target=self._generar_pedidos_cliente,
                args=(i+1,),
                daemon=True
            )
            self.clientes.append(cliente)
            cliente.start()

        # Esperar clientes
        for cliente in self.clientes:
            cliente.join()

        # Señal de cierre
        self.evento_cierre.set()
        
        # Esperar cocineros
        for cocinero in self.cocineros:
            cocinero.join()

        print("\n✨ SIMULACIÓN COMPLETADA CON ÉXITO ✨")

    def _generar_pedidos_cliente(self, cliente_id):
        try:
            for pedido_id in range(1, random.randint(1, MAX_PEDIDOS_POR_CLIENTE)+1):
                if self.evento_cierre.is_set():
                    break
                    
                platos = self._crear_platos(cliente_id, pedido_id)
                for plato in platos:
                    try:
                        self.cola_pedidos.put(plato, timeout=2)
                        with self.lock:
                            print(f"[Cliente {cliente_id}] 📝 Añadió {plato.nombre} "
                                  f"(Prioridad: {plato.prioridad.name})")
                    except queue.Full:
                        with self.lock:
                            print(f"⚠️ Cola llena! Cliente {cliente_id} esperando...")
                        time.sleep(1)
                        continue
                
                time.sleep(random.uniform(0.3, 0.8))
            
            with self.lock:
                print(f"[Cliente {cliente_id}] 🏁 Terminó")
        except Exception as e:
            with self.lock:
                print(f"❌ Error en cliente {cliente_id}: {str(e)}")

    def _crear_platos(self, cliente_id, pedido_id):
        menu_items = [
            ("Pizza", 2.5, Prioridad.MEDIA),
            ("Ensalada", 1.0, Prioridad.BAJA),
            ("Pasta", 3.0, Prioridad.MEDIA),
            ("Sopa", 1.5, Prioridad.ALTA),
            ("Hamburguesa", 2.0, Prioridad.MEDIA),
            ("Filete", 4.0, Prioridad.ALTA)
        ]
        return [
            Plato(
                prioridad=p[2],
                tiempo_coccion=p[1],
                nombre=p[0],
                cliente_id=cliente_id,
                pedido_id=pedido_id
            ) for p in random.choices(menu_items, k=random.randint(1, MAX_PLATOS_POR_PEDIDO))
        ]

    def _trabajar_cocinero(self, cocinero_id):
        try:
            while not self.evento_cierre.is_set() or not self.cola_pedidos.empty():
                try:
                    plato = self.cola_pedidos.get(timeout=1)
                except queue.Empty:
                    continue
                    
                plato.inicio_preparacion = datetime.now()
                
                with self.lock:
                    print(f"\n[Cocinero {cocinero_id}] 🧑🍳 Preparando {plato.nombre} "
                          f"(Prioridad: {plato.prioridad.name})")
                
                time.sleep(plato.tiempo_coccion)
                
                plato.fin_preparacion = datetime.now()
                
                with self.lock:
                    print(f"[Cocinero {cocinero_id}] ✅ Entregó {plato.nombre} "
                          f"en {plato.tiempo_coccion:.1f}s")
                
                self.cola_pedidos.task_done()
        except Exception as e:
            with self.lock:
                print(f"❌ Error en cocinero {cocinero_id}: {str(e)}")

if __name__ == "__main__":
    restaurante = Restaurante()
    restaurante.iniciar_simulacion()