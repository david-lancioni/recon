SET SQL_SAFE_UPDATES = 0;
START TRANSACTION;

-- -----------------------------------------------------
-- Limpeza das tabelas (ordem inversa às dependências)
-- -----------------------------------------------------
DELETE FROM `tb_profile_transaction`;
DELETE FROM `tb_transaction`;
DELETE FROM `tb_rule_field`;
DELETE FROM `tb_aggregation`;
DELETE FROM `tb_rule_type`;
DELETE FROM `tb_rule`;
DELETE FROM `tb_operator`;
DELETE FROM `tb_field`;
DELETE FROM `tb_field_type`;
DELETE FROM `tb_ds`;
DELETE FROM `tb_ds_type`;
DELETE FROM `tb_side`;
DELETE FROM `tb_log`;
DELETE FROM `tb_recon`;
DELETE FROM `tb_user`;
DELETE FROM `tb_profile`;


-- -----------------------------------------------------
-- Data for table `tb_profile`
-- -----------------------------------------------------
INSERT INTO `tb_profile` (`id`, `name`) VALUES (1, 'Administrador');
INSERT INTO `tb_profile` (`id`, `name`) VALUES (2, 'Usuário');


-- -----------------------------------------------------
-- Data for table `tb_user`
-- -----------------------------------------------------
INSERT INTO `tb_user` (`id`, `id_profile`, `name`, `username`, `password`) VALUES (1, 1, 'Administrador', 'admin', 'admin');
INSERT INTO `tb_user` (`id`, `id_profile`, `name`, `username`, `password`) VALUES (2, 2, 'Demo', 'demo', 'demo');


-- -----------------------------------------------------
-- Data for table `tb_recon`
-- -----------------------------------------------------
INSERT INTO `tb_recon` (`id`, `id_user`, `name`, `description`) VALUES (1, 1, 'Saldos x Extrato', 'Conciliação para demonstração');


-- -----------------------------------------------------
-- Data for table `tb_side`
-- -----------------------------------------------------
INSERT INTO `tb_side` (`id`, `name`) VALUES (1, 'Lado 1');
INSERT INTO `tb_side` (`id`, `name`) VALUES (2, 'Lado 2');


-- -----------------------------------------------------
-- Data for table `tb_ds_type`
-- -----------------------------------------------------
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (1, 'Arquivo');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (2, 'Json');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (3, 'Mysql');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (4, 'Postgres');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (5, 'Sql Server');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (6, 'Oracle');
INSERT INTO `tb_ds_type` (`id`, `name`) VALUES (7, 'SQLite');


-- -----------------------------------------------------
-- Data for table `tb_ds`
-- -----------------------------------------------------
INSERT INTO `tb_ds` (`id`, `id_recon`, `id_side`, `id_type`, `name`, `credentials`, `query`, `filename`, `delimiter`, `url`) VALUES (1, 1, 1, 1, 'Saldos', NULL, NULL, 'saldos.csv', ';', NULL);
INSERT INTO `tb_ds` (`id`, `id_recon`, `id_side`, `id_type`, `name`, `credentials`, `query`, `filename`, `delimiter`, `url`) VALUES (2, 1, 2, 1, 'Extrato', NULL, NULL, 'extrato.csv', ';', NULL);


-- -----------------------------------------------------
-- Data for table `tb_field_type`
-- -----------------------------------------------------
INSERT INTO `tb_field_type` (`id`, `name`) VALUES (1, 'Inteiro');
INSERT INTO `tb_field_type` (`id`, `name`) VALUES (2, 'Decimal');
INSERT INTO `tb_field_type` (`id`, `name`) VALUES (3, 'Texto');
INSERT INTO `tb_field_type` (`id`, `name`) VALUES (4, 'Data');


-- -----------------------------------------------------
-- Data for table `tb_field`
-- -----------------------------------------------------
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (1, 1, 1, 'Agencia', 1, NULL);
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (2, 1, 2, 'Conta', 1, NULL);
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (3, 1, 3, 'Valor', 3, NULL);
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (4, 2, 1, 'Agencia', 1, NULL);
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (5, 2, 2, 'Conta', 1, NULL);
INSERT INTO `tb_field` (`id`, `id_ds`, `position`, `name`, `id_field_type`, `value`) VALUES (6, 2, 3, 'Valor', 3, NULL);


-- -----------------------------------------------------
-- Data for table `tb_operator`
-- -----------------------------------------------------
INSERT INTO `tb_operator` (`id`, `name`) VALUES (1, '=');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (2, '<>');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (3, '>');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (4, '>=');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (5, '<');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (6, '<=');
INSERT INTO `tb_operator` (`id`, `name`) VALUES (7, '<>');


-- -----------------------------------------------------
-- Data for table `tb_rule`
-- -----------------------------------------------------
INSERT INTO `tb_rule` (`id`, `id_recon`, `name`) VALUES (1, 1, 'Batimento de arquivos');


-- -----------------------------------------------------
-- Data for table `tb_rule_type`
-- -----------------------------------------------------
INSERT INTO `tb_rule_type` (`id`, `name`) VALUES (1, 'Chave de Batimento');
INSERT INTO `tb_rule_type` (`id`, `name`) VALUES (2, 'Critério de Comparação');


-- -----------------------------------------------------
-- Data for table `tb_aggregation`
-- -----------------------------------------------------
INSERT INTO `tb_aggregation` (`id`, `name`) VALUES (1, 'Somar');
INSERT INTO `tb_aggregation` (`id`, `name`) VALUES (2, 'Maximo');
INSERT INTO `tb_aggregation` (`id`, `name`) VALUES (3, 'Minimo');
INSERT INTO `tb_aggregation` (`id`, `name`) VALUES (4, 'Média');


-- -----------------------------------------------------
-- Data for table `tb_rule_field`
-- -----------------------------------------------------
INSERT INTO `tb_rule_field` (`id`, `id_rule`, `id_rule_type`, `id_field_1`, `id_field_2`, `tolerance`, `id_operator`, `id_aggregation`) VALUES (1, 1, 1, 1, 1, NULL, 1, NULL);
INSERT INTO `tb_rule_field` (`id`, `id_rule`, `id_rule_type`, `id_field_1`, `id_field_2`, `tolerance`, `id_operator`, `id_aggregation`) VALUES (2, 1, 1, 2, 2, NULL, 1, NULL);
INSERT INTO `tb_rule_field` (`id`, `id_rule`, `id_rule_type`, `id_field_1`, `id_field_2`, `tolerance`, `id_operator`, `id_aggregation`) VALUES (3, 1, 2, 3, 3, NULL, 1, 1);


-- -----------------------------------------------------
-- Data for table `tb_transaction`
-- -----------------------------------------------------
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (1, 0, 'Administrador', NULL);
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (2, 1, 'Perfil', 'profile');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (3, 1, 'Transação', 'transaction');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (4, 1, 'Perfil x Transação', 'profile_transaction');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (5, 0, 'Configuração', NULL);
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (6, 5, 'Conciliação', 'recon');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (7, 5, 'Fonte de Dados', 'ds');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (8, 5, 'Campos', 'field');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (9, 5, 'Regras', 'rule');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (10, 5, 'Definição de Regras', 'rule_field');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (12, 0, 'Conciliação', NULL);
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (11, 12, 'Executar', 'run');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (13, 12, 'Sintético', 'report_sintetic');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (14, 12, 'Analitico', 'report_analitic');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (15, 12, 'Logs', 'report_log');
INSERT INTO `tb_transaction` (`id`, `id_parent`, `name`, `link`) VALUES (16, 1, 'Usuário', 'user');


-- -----------------------------------------------------
-- Data for table `tb_profile_transaction`
-- -----------------------------------------------------
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (1, 1, 1);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (2, 1, 2);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (3, 1, 3);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (4, 1, 4);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (5, 1, 5);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (6, 1, 6);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (7, 1, 7);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (8, 1, 8);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (9, 1, 9);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (10, 1, 10);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (11, 1, 11);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (12, 1, 12);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (13, 1, 13);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (14, 1, 14);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (15, 1, 15);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (16, 1, 16);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (17, 2, 12);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (18, 2, 11);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (19, 2, 13);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (20, 2, 14);
INSERT INTO `tb_profile_transaction` (`id`, `id_profile`, `id_transaction`) VALUES (21, 2, 15);

COMMIT;
SET SQL_SAFE_UPDATES = 1;
