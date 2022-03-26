#!/usr/bin/env python3
# Copyright (c) 2017-2019 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Un ejemplo de como crear transacciones P2TR, firmarlas y publicarlas
utilizando el framework funcional.
Trabajo en proceso, sin garantía de funcionar, sigo aprendiendo de Bitcoin y
del framework.
"""
# Imports en orden PEP8 std library primero, después de terceros y 
# finalmente locales


# Evitar importaciones wildcard *
from audioop import add
from test_framework.blocktools import COINBASE_MATURITY
from test_framework.messages import COIN

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from test_framework.descriptors import descsum_create

# Mi clase de prueba hereda de BitcoinTestFramework
class ExampleTest(BitcoinTestFramework):

    def set_test_params(self):
        """Este método debe ser sobrescrito para setear los parámetros de la
        prueba."""
        # Cadena nueva, 1 solo nodo de bitcoind y con los parámetros en la línea de
        # comandos necesarios para taproot
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.extra_args = [["-vbparams=taproot:1:1", "-addresstype=bech32m", "-changetype=bech32m"]]

    def run_test(self):
        """Main test logic"""
        self.log.info("Prueba iniciando!")

        self.log.info("Creamos billetera que funciona con descriptores")
        self.nodes[0].createwallet(wallet_name="TapRoot", descriptors=True, blank=True)

        # importamos la semilla y el XPRIV usando la página https://iancoleman.io/bip39/
        seed = 'ca7d2af0ab7a04857c22bddf064dedc54945f9d6485970b91253ebe0adf132370fee5eb76a123179edc504158bad630c5070a429becdf8a1cbf90595a07591cc'
        xpriv = 'tprv8ZgxMBicQKsPf2h5QMyUYcsbeu8jfz6tR7a7jJpvhBaPJsddMfZdYdhH7mrXPve58KTicWsrJPGEC1XSkHMhHoMxyUuauDWVtvAFvQFNsrM'
        # Derivation path de taproot
        derivation_path = "/86'/1'/0'/0/*"
        # Crear descriptor
        descriptor = f"tr({xpriv}{derivation_path})"
        # generar el checksum
        descriptor_checksum = descsum_create(descriptor)

        # importar el descriptor
        res = self.nodes[0].importdescriptors([
            {
                "desc": descriptor_checksum,
                "active": True,
                "timestamp": "now"
            }])

        # obtener la billetera que creamos
        wallet = self.nodes[0].get_wallet_rpc("TapRoot")

        # Generar una direccion para recibir los fondos de la transaccion COINBASE
        address = wallet.getnewaddress(address_type='bech32m')

        self.log.info("Crear algunos bloques 101 y hacer que madure el bloque1")  
        blocks = self.generatetoaddress(self.nodes[0], COINBASE_MATURITY + 1, address)      

        # Después de generar 101 bloques  hay un UTXO del bloque 1 por 50BTC
        utxos = self.nodes[0].listunspent()
        assert len(utxos) == 1
        assert_equal(utxos[0]["amount"], 50) 

        self.log.info("Seleccionar el UTXO que buscamos")
        utxo = utxos[0]
        self.log.info(f"UTXOs selecionado: {utxo}")

        # Generar la dirección de destino de nuestra nuva transacción
        destination_address = self.nodes[0].getnewaddress(address_type='bech32m')

        tx = self.nodes[0].createrawtransaction([{"txid": utxo["txid"], "vout": utxo["vout"]}], {destination_address: 49.999})
        signed_tx = self.nodes[0].signrawtransactionwithwallet(tx)['hex']
        self.log.info(f"Transacción HEX firmada: {tx}")
        txid = self.nodes[0].sendrawtransaction(signed_tx)
        self.log.info(f"Transacción Id: {txid}")
      
        decrawtx = self.nodes[0].decoderawtransaction(signed_tx, True)
        descriptor = decrawtx['vout'][0]['scriptPubKey']['desc']
        # Guardemos el descriptor
        self.log.info(f"descriptor: {descriptor}".format(descriptor))
        self.log.info(f"Transacción Decodificada: { decrawtx }")
        
        mempool = self.nodes[0].getrawmempool()
        # asegurar que nuestra transacción está en el mempool
        assert_equal(mempool[0], txid)

        self.log.info("Generar un bloque para que se procese nuestra transacción")        
        blocks = self.generate(self.nodes[0], 1)
        self.log.info(f"Bloque: {blocks}")
        
        # Asegurar que nuestra transacción se minó
        mempool = self.nodes[0].getrawmempool()
        assert len(mempool) == 0

        # Verificar que nuestra transacción movió los BTC a la dirección
        # de destino
        transactions = self.nodes[0].listtransactions()
        assert_equal(transactions[9]["address"], destination_address)
        # self.nodes[0].importaddress(destination_address)




        # Verificar que existe un UTXO con la dirección de destino que generamos para la transacción
        utxos = self.nodes[0].listunspent(minconf=0)
        assert len(utxos) > 0
        assert_equal(utxos[0]["address"], destination_address)
        self.log.info(f"UTXOs de nuestra transacción: {utxos[0]}")

if __name__ == '__main__':
    ExampleTest().main()