# Bitcoin Funtional Test Framework

Introducción al Framework de pruebas funcionales de Bitcoin

El framework se compone de una serie de clases y funciones de ayuda (Helper Functions). En estas notas presentaremos las clases con sus atributos y funciones priicipales, para una referencia completa es importante revisar el código que se encuentra en el directorio __bitcoin/test/functionaltest_framework__ del [código fuente de _Bitcoin core_](https://github.com/bitcoin/bitcoin/tree/master/test/functional). 

A continuación se presentan las clases principales, toda prueba debe ser una clase que hereda de la clase _BitcoinTestFramework_, en el ejemplo esta clase es _TestCase_.  Esta nueva clase _TestCase_ debe sobreescribir las member functions **set_test_params** y **run_test**. Del mismo modo, se pueden sobreescribir las funciones que se listan en la sección **Operaciones a sobreescribir**.  Esta es la clase prinicpal que controla la prueba y tiene 3 parámetros principales: 

* _chain_ que por default esta configurada para _'regtest'_ 
* _setup_clean_chain_ que se usa para definir una cadena de bloques iniciando desde el _Genesis block_ si se configura como 'true', de lo contrario si la configuramos como 'false' el framework cargará 200 bloques de una cadena preminada desde el disco cuyas recompensas de minado se distribuyen entre 4 nodos. Cada nodo tiene 25 bloques con subsidio maduros (mas de 100 confirmaciones) igual a 25 x 50 = 1,250 bitcoins en su billetera.
* _nodes_ que determina el número de nodos a instanciar para la prueba


![Example image](img/test-framework-main-classes.png)

Típicamente estos parámetros se configuran en la función __set_test_params__

Ejemplo:
``` python
def set_test_params(self):
        """Override test parameters for your individual test.
        This method must be overridden and num_nodes must be explicitly set."""
        # Si inicias con una blockchain nueva ninguno de los nodos tendrá 
        # bitcoin. 
        self.setup_clean_chain = True

        # Vamos a configurar 3 nodos conectados por default
        self.num_nodes = 3

        # Usa self.extra_args para cambiar los argumentos de línea de comado para
        # cada nodo por posición, para ver los argumentos puedes revisar el archivo
        # [src/init.cpp]
        self.extra_args = [[], ["-logips"], []]
```