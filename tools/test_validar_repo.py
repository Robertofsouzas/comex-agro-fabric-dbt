"""Testes do verificador do repositório (tools/validar_repo.py).

Cada teste monta um repositório de exemplo numa pasta temporária e confere
o que o verificador encontra. Rodar a partir da raiz do repositório:

    python -m unittest tools.test_validar_repo -v
"""
import tempfile
import unittest
from pathlib import Path

from tools.validar_repo import main, validar_repo


def escrever(raiz: str, caminho: str, texto: str) -> None:
    arquivo = Path(raiz) / caminho
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(texto, encoding="utf-8")


class TesteBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()


class TesteR2R3(TesteBase):
    def test_repo_vazio_sem_problemas(self):
        self.assertEqual(validar_repo(self.raiz), [])

    def test_r2_json_invalido(self):
        escrever(self.raiz, "Processing/Pipelines/pl_x.DataPipeline/pipeline-content.json", "{ruim")
        probs = validar_repo(self.raiz)
        self.assertEqual(len(probs), 1)
        self.assertTrue(probs[0].startswith("R2 Processing/Pipelines/pl_x.DataPipeline/pipeline-content.json:"))

    def test_r2_cobre_platform_pbir_pbism(self):
        for nome in (".platform", "definition.pbir", "definition.pbism"):
            escrever(self.raiz, f"Visualization/Reports/r.Report/{nome}", "nao e json")
        self.assertEqual(sum(p.startswith("R2 ") for p in validar_repo(self.raiz)), 3)

    def test_r2_json_com_bom_passa(self):
        escrever(self.raiz, "a/b.json", "﻿{\"ok\": 1}")
        self.assertEqual(validar_repo(self.raiz), [])

    def test_r3_workspaceid_real_no_pipeline(self):
        escrever(self.raiz, "Processing/Pipelines/pl_x.DataPipeline/pipeline-content.json",
                 '{"a": {"workspaceId": "11111111-1111-1111-1111-111111111111"}}')
        self.assertTrue(any(p.startswith("R3 ") for p in validar_repo(self.raiz)))

    def test_r3_workspaceid_zerado_passa(self):
        escrever(self.raiz, "Processing/Pipelines/pl_x.DataPipeline/pipeline-content.json",
                 '{"a": {"workspaceId": "00000000-0000-0000-0000-000000000000"}}')
        self.assertEqual(validar_repo(self.raiz), [])

    def test_main_codigo_de_saida(self):
        self.assertEqual(main([self.raiz]), 0)
        escrever(self.raiz, "x.json", "{")
        self.assertEqual(main([self.raiz]), 1)


class TesteR1(TesteBase):
    # Os textos são montados por concatenação para não plantar um "segredo"
    # de verdade neste arquivo (o próprio verificador o reprovaria).
    def test_r1_padroes(self):
        casos = {
            "a.py": "client" + "_secret = 'abcd1234efgh5678'",
            "b.ps1": "pass" + "word=Segredo123",
            "c.txt": "Authorization: Bear" + "er eyJ" + "a" * 40,
            "d.cfg": "Account" + "Key=" + "Q" * 40,
            "e.txt": "sv=2024&s" + "ig=" + "A" * 30,
            "f.pem": "-----BEGIN RSA " + "PRIVATE KEY-----",
        }
        for nome, texto in casos.items():
            escrever(self.raiz, nome, texto)
        self.assertEqual(sum(p.startswith("R1 ") for p in validar_repo(self.raiz)), 6)

    def test_r1_palavra_sem_valor_passa(self):
        escrever(self.raiz, "README.md", "Sem senhas, tokens ou password no repositório.")
        self.assertEqual(validar_repo(self.raiz), [])

class TesteRegrasComex(TesteBase):
    GUID = "11111111-1111-1111-1111-111111111111"

    def test_r1_tokens_do_github(self):
        escrever(self.raiz, "a.txt", "gh" + "p_" + "a" * 36)
        escrever(self.raiz, "b.txt", "github_" + "pat_" + "A1" * 20)
        self.assertEqual(sum(p.startswith("R1 ") for p in validar_repo(self.raiz)), 2)

    def test_r7_tenant_reprova_mesmo_em_arquivo_liberado(self):
        escrever(self.raiz, "fabric/vl_comex.VariableLibrary/variables.json", '{"tenantId": "%s"}' % self.GUID)
        escrever(self.raiz, "a.txt", "https://login.microsoftonline.com/" + self.GUID)
        self.assertEqual(sum(p.startswith("R7 ") for p in validar_repo(self.raiz)), 2)

    def test_r8_endereco_sql_do_fabric(self):
        escrever(self.raiz, "fabric/x.json", '{"endpoint": "abc123-xyz.datawarehouse.' + 'fabric.microsoft.com"}')
        self.assertEqual(sum(p.startswith("R8 ") for p in validar_repo(self.raiz)), 1)

    def test_r9_profiles_so_em_ci(self):
        escrever(self.raiz, "ci/profiles.yml", "comex_agro:\n  target: ci\n")
        self.assertEqual(validar_repo(self.raiz), [])
        escrever(self.raiz, "profiles.yml", "comex_agro:\n  target: dev\n")
        self.assertTrue(any(p.startswith("R9 profiles.yml:0:") for p in validar_repo(self.raiz)))


class TesteExcecaoDoDbtJob(TesteBase):
    """O Fabric grava no dbt job o ID do workspace e o endereço SQL: liberados só ali e só nessas chaves."""

    ARQUIVO = "fabric/Processing/dbt/dbtj_comex.DataBuildToolJob/dbt-content.json"
    GUID = "11111111-1111-1111-1111-111111111111"
    # Partido para este arquivo não conter um endereço que o próprio verificador reprove.
    ENDERECO = "abc123-xyz.datawarehouse." + "fabric.microsoft.com"

    def regras(self):
        return sorted(p.split(" ", 1)[0] for p in validar_repo(self.raiz))

    def conteudo(self, chave_id="workspaceId", chave_endereco="endPoint"):
        return '{\n  "%s": "%s",\n  "%s": "%s"\n}\n' % (chave_id, self.GUID, chave_endereco, self.ENDERECO)

    def test_arquivo_observado_passa(self):
        escrever(self.raiz, self.ARQUIVO, self.conteudo())
        self.assertEqual(validar_repo(self.raiz), [])

    def test_outro_caminho_continua_reprovando(self):
        escrever(self.raiz, "fabric/Processing/dbt/outro.DataBuildToolJob/dbt-content.json", self.conteudo())
        self.assertEqual(self.regras(), ["R4", "R8"])

    def test_outras_chaves_no_mesmo_arquivo_reprovam(self):
        escrever(self.raiz, self.ARQUIVO, self.conteudo(chave_id="outroId", chave_endereco="server"))
        self.assertEqual(self.regras(), ["R4", "R8"])

    def test_tenant_continua_reprovando_no_arquivo_liberado(self):
        escrever(self.raiz, self.ARQUIVO, '{"tenantId": "%s"}' % self.GUID)
        self.assertIn("R7", self.regras())


class TesteR4R6(TesteBase):
    def test_r4_guid_solto_reprova(self):
        escrever(self.raiz, "Processing/Notebooks/n.Notebook/notebook-content.py",
                 "caminho = 'abfss://11111111-1111-1111-1111-111111111111@onelake'")
        self.assertTrue(any(p.startswith("R4 Processing/Notebooks/") for p in validar_repo(self.raiz)))

    def test_r4_arquivo_de_testes_so_aceita_guid_falso(self):
        # Textos partidos para este arquivo não conter um GUID que o próprio verificador reprove.
        arquivo = "tools/test_validar_repo.py"
        escrever(self.raiz, arquivo, "X = '" + "11111111-1111-1111-1111-" + "111111111111'")
        self.assertEqual(validar_repo(self.raiz), [])
        escrever(self.raiz, arquivo, "X = '" + "4a7c1f3e-9b2d-4e6a-" + "8c1f-5d0b3a9e7c24'")
        self.assertTrue(any(p.startswith(f"R4 {arquivo}:1:") for p in validar_repo(self.raiz)))

    def test_r4_logicalid_passa(self):
        escrever(self.raiz, "x/.platform", '{"config": {"logicalId": "11111111-1111-1111-1111-111111111111"}}')
        self.assertEqual(validar_repo(self.raiz), [])

    def test_r4_expressions_tmdl_permitido(self):
        escrever(self.raiz, "Storage/Semantic Models/m.SemanticModel/definition/expressions.tmdl",
                 'expression p_workspace_id = "11111111-1111-1111-1111-111111111111"')
        self.assertEqual(validar_repo(self.raiz), [])

    def test_r4_dois_guids_na_mesma_linha(self):
        escrever(self.raiz, "a.txt", "https://onelake/11111111-1111-1111-1111-111111111111/"
                                      "22222222-2222-2222-2222-222222222222")
        self.assertEqual(sum(p.startswith("R4 a.txt:1:") for p in validar_repo(self.raiz)), 2)

    def test_r6_medida_com_nome_de_coluna(self):
        escrever(self.raiz, "m.SemanticModel/definition/tables/t.tmdl",
                 "table t\n\tmeasure 'Quantidade' = SUM(t[quantidade])\n\tcolumn quantidade\n")
        self.assertTrue(any(p.startswith("R6 ") for p in validar_repo(self.raiz)))

    def test_r6_var_reservada(self):
        escrever(self.raiz, "m.SemanticModel/definition/tables/t.tmdl",
                 "table t\n\tmeasure 'X' =\n\t\t\tVAR top = 1\n\t\t\tRETURN top\n")
        self.assertTrue(any("top" in p and p.startswith("R6 ") for p in validar_repo(self.raiz)))


if __name__ == "__main__":
    unittest.main()
