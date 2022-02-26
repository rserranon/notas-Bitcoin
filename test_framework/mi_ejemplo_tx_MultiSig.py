#!/usr/bin/env python3
# Copyright (c) 2017-2019 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Un ejemplo de como crear transacciones Multisig, firmarlas y publicarlas
utilizando el framework funcional.
Trabajo en proceso, sin garantía de funcionar, sigo aprendiendo de Bitcoin y
del framework.
"""
# Imports en orden PEP8 std library primero, después de terceros y 
# finalmente locales


# Evitar importaciones wildcard *
from test_framework.blocktools import COINBASE_MATURITY

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

# Mi clase de prueba hereda de BitcoinTestFramework
class ExampleTest(BitcoinTestFramework):

    def set_test_params(self):
        """Este método debe ser sobrescrito para setear los parámetros de la
        prueba."""
        # Cadena nueva, 3 nodos de bitcoind y no hay parámetros en la línea de
        # comandos para los nodos
        self.setup_clean_chain = True
        self.num_nodes = 3
        self.extra_args = [[],[],[]]

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()


    def run_test(self):
        """Main test logic"""
        self.log.info("Prueba iniciando!")
        self.log.info("Crear algunos bloques 101 y hacer que madure el bloque1")        
        blocks = self.generate(self.nodes[0], COINBASE_MATURITY + 1)

        # Después de generar 101 bloques  hay un UTXO del bloque 1 por 50BTC
        utxos = self.nodes[0].listunspent()
        assert len(utxos) == 1
        assert_equal(utxos[0]["amount"], 50) 

        node0, node1, node2 = self.nodes
        publicK0 = node0.getaddressinfo(node0.getnewaddress())['pubkey']
        publicK1 = node1.getaddressinfo(node1.getnewaddress())['pubkey']
        publicK2 = node2.getaddressinfo(node2.getnewaddress())['pubkey']
        keys=[publicK0, publicK1, publicK2]
        # Crear la transacción multifirma con 2 de las 3 llaves (2/3)
        multi_sig = node0.createmultisig(2, keys, 'legacy')
        # obtener la dirección de destino
        destination_addr = multi_sig['address']
        # obtener el descritor para las verificaciones
        descriptor = multi_sig['descriptor']
        target_address = self.nodes[0].deriveaddresses(descriptor)
        assert_equal(target_address[0], destination_addr)
        self.log.info("Destination Address: {}".format(destination_addr))

        txid = node0.sendtoaddress(destination_addr, 40)
        tx = node0.getrawtransaction(txid, True)
        self.log.info("Transacción Decodificada: {}".format(tx))
        
        # buscar la destination_addr en los vouts de la tx
        vout = [v["n"] for v in tx["vout"] if destination_addr == v["scriptPubKey"]["address"]]
        assert len(vout) == 1
        vout = vout[0]
        tx_address = tx["vout"][vout]["scriptPubKey"]["address"]
        # validar que la dirección de la transacción es igual a la de destino
        assert_equal(tx_address,destination_addr)

        mempool = self.nodes[0].getrawmempool()
        # asegurar que nuestra transacción está en el mempool
        assert_equal(mempool[0], txid)

        self.log.info("Generar un bloque para que se procese nuestra transacción")        
        self.generate(node0, 1)
        
        # Asegurar que nuestra transacción se minó
        mempool = self.nodes[0].getrawmempool()
        assert len(mempool) == 0

        # Verificar que nuestra transacción movió los BTC a la dirección
        # de destino
        transactions = self.nodes[0].listtransactions()
        assert_equal(transactions[8]["address"], destination_addr)
        
        # TODO entender por qué que nuestra transacción no aparece en los UTXOs 
        # de esta wallet
        utxos = self.nodes[0].listunspent(minconf=0)
        assert len(utxos) > 0
        self.log.info("UTXOs disponibles: {}".format(utxos))

        # Escanear el UTXOs set usando el descriptor
        utxo_esperado = self.nodes[0].scantxoutset(action="start", scanobjects=[{'desc': descriptor}])
        utxo_address = self.nodes[0].deriveaddresses(utxo_esperado['unspents'][0]['desc'])
        # Verificar que la dirección de destino coincide con la dirección del descriptor
        assert_equal(utxo_address[0], destination_addr)
        self.log.info("UTXO esperado: {}".format(utxo_esperado['unspents'][0]['desc']))

if __name__ == '__main__':
    ExampleTest().main()