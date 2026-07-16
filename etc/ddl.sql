-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Table `tb_aggregation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_aggregation` ;

CREATE TABLE IF NOT EXISTS `tb_aggregation` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_profile`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_profile` ;

CREATE TABLE IF NOT EXISTS `tb_profile` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_user` ;

CREATE TABLE IF NOT EXISTS `tb_user` (
  `id` INT NOT NULL,
  `id_profile` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(50) NOT NULL,
  `password` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_user_email` (`email` ASC) VISIBLE,
  INDEX `fk_user_profile_idx` (`id_profile` ASC) VISIBLE,
  CONSTRAINT `fk_user_profile`
    FOREIGN KEY (`id_profile`)
    REFERENCES `tb_profile` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_recon`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_recon` ;

CREATE TABLE IF NOT EXISTS `tb_recon` (
  `id` INT NOT NULL,
  `id_user` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  `description` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_recon_user_idx` (`id_user` ASC) VISIBLE,
  CONSTRAINT `fk_recon_user`
    FOREIGN KEY (`id_user`)
    REFERENCES `tb_user` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_side`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_side` ;

CREATE TABLE IF NOT EXISTS `tb_side` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_ds_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_ds_type` ;

CREATE TABLE IF NOT EXISTS `tb_ds_type` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_ds`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_ds` ;

CREATE TABLE IF NOT EXISTS `tb_ds` (
  `id` INT NOT NULL,
  `id_recon` INT NOT NULL,
  `id_side` INT NOT NULL,
  `id_type` INT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `credentials` VARCHAR(500) NULL DEFAULT NULL,
  `query` TEXT NULL DEFAULT NULL,
  `filename` VARCHAR(50) NULL DEFAULT NULL,
  `delimiter` VARCHAR(10) NULL DEFAULT NULL,
  `url` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_ds_recon_idx` (`id_recon` ASC) VISIBLE,
  INDEX `fk_ds_side_idx` (`id_side` ASC) VISIBLE,
  INDEX `fk_ds_ds_type_idx` (`id_type` ASC) VISIBLE,
  CONSTRAINT `fk_ds_recon`
    FOREIGN KEY (`id_recon`)
    REFERENCES `tb_recon` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_ds_side`
    FOREIGN KEY (`id_side`)
    REFERENCES `tb_side` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_ds_ds_type`
    FOREIGN KEY (`id_type`)
    REFERENCES `tb_ds_type` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_field_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_field_type` ;

CREATE TABLE IF NOT EXISTS `tb_field_type` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_field`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_field` ;

CREATE TABLE IF NOT EXISTS `tb_field` (
  `id` INT NOT NULL,
  `id_ds` INT NOT NULL,
  `position` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  `id_field_type` INT NOT NULL,
  `value` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_field_ds_idx` (`id_ds` ASC) VISIBLE,
  INDEX `fk_field_field_type_idx` (`id_field_type` ASC) VISIBLE,
  CONSTRAINT `fk_field_ds`
    FOREIGN KEY (`id_ds`)
    REFERENCES `tb_ds` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_field_field_type`
    FOREIGN KEY (`id_field_type`)
    REFERENCES `tb_field_type` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_log`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_log` ;

CREATE TABLE IF NOT EXISTS `tb_log` (
  `id_user` INT NOT NULL,
  `id_recon` INT NOT NULL,
  `level` VARCHAR(50) NOT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  `class_name` VARCHAR(50) NULL DEFAULT NULL,
  `method_name` VARCHAR(50) NULL DEFAULT NULL,
  `message` TEXT NULL DEFAULT NULL,
  INDEX `fk_log_user_idx` (`id_user` ASC) VISIBLE,
  INDEX `fk_log_recon_idx` (`id_recon` ASC) VISIBLE,
  CONSTRAINT `fk_log_recon`
    FOREIGN KEY (`id_recon`)
    REFERENCES `tb_recon` (`id`),
  CONSTRAINT `fk_log_user`
    FOREIGN KEY (`id_user`)
    REFERENCES `tb_user` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_operator`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_operator` ;

CREATE TABLE IF NOT EXISTS `tb_operator` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_rule`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_rule` ;

CREATE TABLE IF NOT EXISTS `tb_rule` (
  `id` INT NOT NULL,
  `id_recon` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_rule_recon_idx` (`id_recon` ASC) VISIBLE,
  CONSTRAINT `fk_rule_recon`
    FOREIGN KEY (`id_recon`)
    REFERENCES `tb_recon` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_rule_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_rule_type` ;

CREATE TABLE IF NOT EXISTS `tb_rule_type` (
  `id` INT NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_rule_field`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_rule_field` ;

CREATE TABLE IF NOT EXISTS `tb_rule_field` (
  `id` INT NOT NULL,
  `id_rule` INT NOT NULL,
  `id_rule_type` INT NOT NULL,
  `id_field_1` INT NOT NULL,
  `id_field_2` INT NOT NULL,
  `tolerance` DOUBLE NULL DEFAULT '0',
  `id_operator` INT NOT NULL DEFAULT '1',
  `id_aggregation` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_rule_field_rule_idx` (`id_rule` ASC) VISIBLE,
  INDEX `fk_rule_field_rule_type_idx` (`id_rule_type` ASC) VISIBLE,
  INDEX `fk_rule_field_operator_idx` (`id_operator` ASC) VISIBLE,
  INDEX `fk_rule_field_aggregation_idx` (`id_aggregation` ASC) VISIBLE,
  INDEX `fk_rule_field_field_1_idx` (`id_field_1` ASC) VISIBLE,
  INDEX `fk_rule_field_field_2_idx` (`id_field_2` ASC) VISIBLE,
  CONSTRAINT `fk_rule_field_operator`
    FOREIGN KEY (`id_operator`)
    REFERENCES `tb_operator` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_rule_field_rule`
    FOREIGN KEY (`id_rule`)
    REFERENCES `tb_rule` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_rule_field_rule_type`
    FOREIGN KEY (`id_rule_type`)
    REFERENCES `tb_rule_type` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_rule_field_aggregation`
    FOREIGN KEY (`id_aggregation`)
    REFERENCES `tb_aggregation` (`id`),
  CONSTRAINT `fk_rule_field_field_1`
    FOREIGN KEY (`id_field_1`)
    REFERENCES `tb_field` (`id`),
  CONSTRAINT `fk_rule_field_field_2`
    FOREIGN KEY (`id_field_2`)
    REFERENCES `tb_field` (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_transaction`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_transaction` ;

CREATE TABLE IF NOT EXISTS `tb_transaction` (
  `id` INT NOT NULL,
  `id_parent` INT NULL DEFAULT NULL,
  `name` VARCHAR(50) NULL DEFAULT NULL,
  `link` VARCHAR(200) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `tb_profile_transaction`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tb_profile_transaction` ;

CREATE TABLE IF NOT EXISTS `tb_profile_transaction` (
  `id` INT NOT NULL,
  `id_profile` INT NOT NULL,
  `id_transaction` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_profile_transaction` (`id_profile` ASC, `id_transaction` ASC) VISIBLE,
  INDEX `fk_profile_transaction_profile_idx` (`id_profile` ASC) VISIBLE,
  INDEX `fk_profile_transaction_transaction_idx` (`id_transaction` ASC) VISIBLE,
  CONSTRAINT `fk_profile_transaction_profile`
    FOREIGN KEY (`id_profile`)
    REFERENCES `tb_profile` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_profile_transaction_transaction`
    FOREIGN KEY (`id_transaction`)
    REFERENCES `tb_transaction` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;