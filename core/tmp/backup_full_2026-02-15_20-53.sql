-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: 127.0.0.1    Database: flask_crud
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `appointments`
--

DROP TABLE IF EXISTS `appointments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `appointments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `client_id` int(11) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `status` enum('scheduled','completed','cancelled','no_show') DEFAULT 'scheduled',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointments`
--

LOCK TABLES `appointments` WRITE;
/*!40000 ALTER TABLE `appointments` DISABLE KEYS */;
/*!40000 ALTER TABLE `appointments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `budget_items`
--

DROP TABLE IF EXISTS `budget_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `budget_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `budget_id` int(11) NOT NULL,
  `product_id` int(11) DEFAULT NULL,
  `service_id` int(11) DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `quantity` decimal(10,2) DEFAULT 1.00,
  `unit_price` decimal(10,2) DEFAULT 0.00,
  `total` decimal(10,2) DEFAULT 0.00,
  `mechanic` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `budget_id` (`budget_id`),
  KEY `product_id` (`product_id`),
  KEY `service_id` (`service_id`),
  CONSTRAINT `budget_items_ibfk_1` FOREIGN KEY (`budget_id`) REFERENCES `budgets` (`id`) ON DELETE CASCADE,
  CONSTRAINT `budget_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `budget_items_ibfk_3` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `budget_items`
--

LOCK TABLES `budget_items` WRITE;
/*!40000 ALTER TABLE `budget_items` DISABLE KEYS */;
INSERT INTO `budget_items` VALUES (1,1,NULL,NULL,'Kit velas',1.00,340.00,340.00,NULL,'2026-02-09 09:22:46'),(2,1,NULL,NULL,'Serviço troca de velas',1.00,80.00,80.00,NULL,'2026-02-09 09:22:46'),(5,3,NULL,NULL,'Kit velas',2.00,340.00,680.00,NULL,'2026-02-09 10:33:54'),(6,3,NULL,NULL,'troca de vela e manutenção',2.00,127.00,254.00,NULL,'2026-02-09 10:33:54'),(7,4,NULL,NULL,'troca de oléo 5w30',4.00,20.00,80.00,NULL,'2026-02-09 10:40:58'),(8,2,NULL,NULL,'Troca de suspensão',180.00,2.00,360.00,NULL,'2026-02-09 12:08:14'),(9,2,NULL,NULL,'Troca do cubo de roda',2.00,90.00,180.00,NULL,'2026-02-09 12:08:14'),(10,5,NULL,NULL,'Junta de cabeçote',1.00,295.00,295.00,NULL,'2026-02-09 13:21:24'),(11,5,NULL,NULL,'Troca de Eixo dianteiro',1.00,195.00,195.00,NULL,'2026-02-09 13:21:24'),(12,6,NULL,NULL,'Reparo do amortecedor',95.00,4.00,380.00,NULL,'2026-02-09 13:28:24'),(13,6,NULL,NULL,'Óleo 5w30',4.00,30.00,120.00,NULL,'2026-02-09 13:28:24'),(14,6,NULL,NULL,'Serviço de troca de Óleo',80.00,1.00,80.00,NULL,'2026-02-09 13:28:24'),(15,7,NULL,NULL,'Junta de cabeçote',1.00,95.00,95.00,NULL,'2026-02-09 13:29:39'),(16,7,NULL,NULL,'Óleo 5w30',4.00,30.00,120.00,NULL,'2026-02-09 13:29:39'),(17,7,NULL,NULL,'Serviço de suspensão',130.00,2.00,260.00,NULL,'2026-02-09 13:29:39'),(18,8,NULL,NULL,'Troca de Alavanca do Freio de mão',1.00,100.00,100.00,NULL,'2026-02-11 17:37:53'),(22,9,NULL,NULL,'Serviço troca do cutelo valvola',1.00,50.00,50.00,NULL,'2026-02-13 14:53:02'),(23,9,NULL,NULL,'Cotovelo da valvula ( pedido )',1.00,15.00,15.00,NULL,'2026-02-13 14:53:02'),(24,10,NULL,NULL,'kit velas',1.00,20.00,20.00,NULL,'2026-02-14 12:28:05');
/*!40000 ALTER TABLE `budget_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `budgets`
--

DROP TABLE IF EXISTS `budgets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `budgets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `vehicle_id` int(11) DEFAULT NULL,
  `vehicle_km` int(11) DEFAULT NULL,
  `status` enum('draft','sent','approved','rejected','ready_for_pickup','delivered','completed') NOT NULL DEFAULT 'draft',
  `approval_status` enum('approved','rejected','sent') NOT NULL DEFAULT 'sent',
  `stage_status` enum('budget','delivered','ready_for_pickup') NOT NULL DEFAULT 'budget',
  `approved_at` datetime DEFAULT NULL,
  `rejected_at` datetime DEFAULT NULL,
  `ready_for_pickup_at` datetime DEFAULT NULL,
  `delivered_at` datetime DEFAULT NULL,
  `total_value` decimal(10,2) DEFAULT 0.00,
  `discount` decimal(10,2) DEFAULT 0.00,
  `notes` text DEFAULT NULL,
  `expiration_date` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `client_id` (`client_id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `budgets_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `budgets_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`),
  CONSTRAINT `budgets_ibfk_3` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `budgets`
--

LOCK TABLES `budgets` WRITE;
/*!40000 ALTER TABLE `budgets` DISABLE KEYS */;
INSERT INTO `budgets` VALUES (1,4,6,1,109800,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,420.00,0.00,'','2026-02-16','2026-02-09 09:22:46','2026-02-15 23:53:25'),(2,4,1,2,18200,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,540.00,0.00,'O cliente comprou as peças por fora','2026-02-16','2026-02-06 09:34:30','2026-02-15 23:53:25'),(3,4,3,3,107222,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,934.00,0.00,'','2026-02-16','2026-02-05 10:33:54','2026-02-15 23:53:25'),(4,4,1,2,50059,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,80.00,0.00,'O cliente troce o óleo','2026-02-16','2026-02-09 10:40:58','2026-02-15 23:53:25'),(5,4,6,4,50050,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,490.00,0.00,'','2026-02-16','2026-02-09 13:21:24','2026-02-15 23:53:25'),(6,4,2,5,140367,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,580.00,0.00,'','2026-02-16','2026-02-09 13:28:24','2026-02-15 23:53:25'),(7,4,2,5,240678,'sent','sent','budget',NULL,NULL,NULL,NULL,475.00,0.00,'','2026-02-16','2026-02-09 13:29:39','2026-02-09 13:29:39'),(8,11,13,6,2400300,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,100.00,0.00,'','2026-02-18','2026-02-11 17:37:53','2026-02-15 23:53:25'),(9,11,16,7,0,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,65.00,0.00,'','2026-02-20','2026-02-13 14:51:20','2026-02-15 23:53:25'),(10,12,17,8,5000,'approved','approved','budget','2026-02-15 20:53:25',NULL,NULL,NULL,20.00,0.00,'','2026-02-21','2026-02-14 12:28:05','2026-02-15 23:53:25');
/*!40000 ALTER TABLE `budgets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_category` (`user_id`,`name`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,4,'Injeção Eletrônica','2026-02-15 23:53:25'),(2,4,'Óleo','2026-02-15 23:53:25'),(3,4,'GOL','2026-02-15 23:53:25'),(4,11,'Óleo','2026-02-15 23:53:25');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `phone1` varchar(20) DEFAULT NULL,
  `phone2` varchar(20) DEFAULT NULL,
  `cpf` varchar(20) DEFAULT NULL,
  `sector` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `cep` varchar(10) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `address_number` varchar(20) DEFAULT NULL,
  `complement` varchar(100) DEFAULT NULL,
  `neighborhood` varchar(100) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `clients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
INSERT INTO `clients` VALUES (1,4,'João da Bezerra','(11) 99999-1234','(11) 3333-0000','123.456.789-00','Varejo','2026-02-09 02:44:10','2026-02-09 03:00:17',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(2,4,'Maria Oliveira','(21) 98888-5555',NULL,'987.654.321-99','Serviços','2026-02-09 02:44:10','2026-02-09 02:57:30',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(3,4,'Tech Solutions Ltda','(31) 97777-8888','(31) 3222-1111','12.345.678/0001-90','Atacado','2026-02-09 02:44:10','2026-01-09 02:57:48',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(4,1,'Padaria do Joaquim','(11) 95555-4444',NULL,'11.222.333/0001-55','Varejo','2026-02-09 02:44:10','2026-02-09 02:44:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(6,4,'Beatriz Silva','(62) 62626-2626','(62) 62626-2626','111.111.111-11','Tiradentes','2026-02-09 02:58:42','2026-02-09 02:58:42',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(7,1,'João da Silva','(11) 99999-1234','(11) 3333-0000','123.456.789-00','Varejo','2026-02-09 09:08:04','2026-02-09 09:08:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(8,1,'Maria Oliveira','(21) 98888-5555',NULL,'987.654.321-99','Serviços','2026-02-09 09:08:04','2026-02-09 09:08:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(9,1,'Tech Solutions Ltda','(31) 97777-8888','(31) 3222-1111','12.345.678/0001-90','Atacado','2026-02-09 09:08:04','2026-02-09 09:08:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(10,1,'Padaria do Joaquim','(11) 95555-4444',NULL,'11.222.333/0001-55','Varejo','2026-02-09 09:08:04','2026-02-09 09:08:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(11,1,'Consultoria ABC','(41) 96666-7777',NULL,'55.666.777/0001-88','Serviços','2026-02-09 09:08:04','2026-02-09 09:08:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(12,4,'Cristiane','(62) 99998-8888','(98) 66664-4444','222.222.222-22','Garavelo','2026-02-09 13:44:05','2026-02-09 13:44:05',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(13,11,'Sebastião Rodrigo','(62) 99857-9084','(62) 99857-9084','010.460.381-99','Buriti Sereno','2026-02-11 17:36:26','2026-02-11 17:36:26',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(14,11,'Construservice','(62) 99999-9999','(62) 88888-8888','77.777.777/7777-77','Jardim Novo Mundo','2026-02-12 22:45:46','2026-02-12 22:46:04',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(15,11,'Mazza Fashion','(62) 99999-9999','(62) 88888-8888','99.999.999/9999-99','Setor Jaó','2026-02-12 22:47:03','2026-02-12 22:47:03',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(16,11,'Viviane EcoSporte','(62) 99423-0809','(62) 99423-0809','777.777.777-77','Não consta','2026-02-13 14:47:29','2026-02-13 14:47:29',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(17,12,'Construservice',NULL,NULL,NULL,NULL,'2026-02-14 12:28:05','2026-02-14 12:28:05',NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `financial_expenses`
--

DROP TABLE IF EXISTS `financial_expenses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `financial_expenses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `category` varchar(50) NOT NULL,
  `payment_type` enum('pix','dinheiro','cartao credito','cartao debito','boleto','transferência') NOT NULL,
  `due_date` date NOT NULL,
  `paid_date` date DEFAULT NULL,
  `status` enum('pending','paid','cancelled') NOT NULL DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `financial_expenses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `financial_expenses`
--

LOCK TABLES `financial_expenses` WRITE;
/*!40000 ALTER TABLE `financial_expenses` DISABLE KEYS */;
/*!40000 ALTER TABLE `financial_expenses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `financial_income`
--

DROP TABLE IF EXISTS `financial_income`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `financial_income` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `budget_id` int(11) DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `category` enum('serviço','contrato','salario mensal','bico') NOT NULL,
  `payment_type` enum('pix','dinheiro','cartao credito','cartao debito','boleto','transferência') NOT NULL,
  `entry_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` enum('pending','received','cancelled') NOT NULL DEFAULT 'received',
  `received_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `fk_financial_income_budget` (`budget_id`),
  CONSTRAINT `financial_income_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_financial_income_budget` FOREIGN KEY (`budget_id`) REFERENCES `budgets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `financial_income`
--

LOCK TABLES `financial_income` WRITE;
/*!40000 ALTER TABLE `financial_income` DISABLE KEYS */;
INSERT INTO `financial_income` VALUES (11,4,NULL,'Salário Fevereiro',5000.00,'salario mensal','transferência','2026-02-05','2026-02-08 17:30:43','received','2026-02-05'),(12,4,NULL,'Projeto Extra',1500.00,'serviço','pix','2026-02-02','2026-02-08 17:30:43','received','2026-02-02'),(16,4,NULL,'Contrato CS',1000.00,'contrato','pix','2026-02-15','2026-02-08 17:52:31','received','2026-02-15'),(20,4,4,'Orçamento #4 - João da Bezerra',80.00,'serviço','cartao credito','2026-02-09','2026-02-09 12:27:49','received','2026-02-09'),(21,4,1,'Orçamento #1 - Beatriz Silva',420.00,'serviço','dinheiro','2026-02-09','2026-02-09 12:28:33','received','2026-02-09'),(22,4,3,'Orçamento #3 - Tech Solutions Ltda',934.00,'serviço','pix','2026-02-09','2026-02-09 12:28:49','received','2026-02-09'),(23,4,5,'Orçamento #5 - Beatriz Silva',490.00,'serviço','pix','2026-02-09','2026-02-09 13:21:34','received','2026-02-09'),(24,11,8,'Orçamento #8 - Sebastião Rodrigo',100.00,'serviço','dinheiro','2026-02-11','2026-02-11 17:38:11','received','2026-02-11'),(33,11,9,'Orçamento #9 - Viviane EcoSporte ( aguardando pag )',65.00,'serviço','pix','2026-01-30','2026-02-13 14:54:14','received','2026-01-30');
/*!40000 ALTER TABLE `financial_income` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `barcode` varchar(100) DEFAULT NULL,
  `quantity` int(11) DEFAULT 0,
  `min_quantity` int(11) DEFAULT 0,
  `cost_price` decimal(10,2) DEFAULT 0.00,
  `sell_price` decimal(10,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  `sku` varchar(50) DEFAULT NULL,
  `min_stock` int(11) DEFAULT 0,
  `images` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`images`)),
  `category_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `supplier_id` (`supplier_id`),
  KEY `fk_product_category` (`category_id`),
  CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `products_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (2,4,1,'Kit velas','Injeção Eletrônica',NULL,7,2,290.00,340.00,'2026-02-09 02:14:56','2026-02-15 23:53:25','PROD-2',0,NULL,NULL),(3,4,1,'Óleo 5w30','Óleo',NULL,10,2,20.00,30.00,'2026-02-09 13:15:07','2026-02-15 23:53:25','PROD-3',0,NULL,NULL),(4,4,1,'Junta de cabeçote GOL','GOL',NULL,10,3,75.00,95.00,'2026-02-09 13:16:34','2026-02-15 23:53:25','PROD-4',0,NULL,NULL),(6,11,2,'Filtro de Óleo WO 140 ( verificar preço )','Óleo',NULL,2,2,10.00,32.00,'2026-02-13 14:23:51','2026-02-15 23:53:25','PROD-6',0,NULL,NULL),(7,11,2,'Filtro de Óleo WO 460 ( verificar preço )','Óleo',NULL,2,2,10.00,32.00,'2026-02-13 14:25:18','2026-02-15 23:53:25','PROD-7',0,NULL,NULL),(9,11,2,'Filtro de Óleo WO 346 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:26:01','2026-02-15 23:53:25','PROD-9',0,NULL,NULL),(10,11,NULL,'Filtro de Óleo WO 240 ( verificar o preço )','',NULL,3,2,10.00,32.00,'2026-02-13 14:27:00','2026-02-15 23:53:25','PROD-10',0,NULL,NULL),(11,11,2,'Filtro de Óleo WO 120 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:29:04','2026-02-15 23:53:25','PROD-11',0,NULL,NULL),(12,11,2,'Filtro de Óleo WO 340( verificar preço )','Óleo',NULL,4,2,10.00,32.00,'2026-02-13 14:29:46','2026-02-15 23:53:25','PROD-12',0,NULL,NULL),(13,11,2,'Filtro de Óleo WO 130 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:30:20','2026-02-15 23:53:25','PROD-13',0,NULL,NULL),(14,11,2,'Filtro de Óleo WO 130 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:31:07','2026-02-15 23:53:25','PROD-14',0,NULL,NULL),(15,11,2,'Filtro de Óleo JFO 211 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:32:29','2026-02-15 23:53:25','PROD-15',0,NULL,NULL),(16,11,2,'Filtro de Óleo JFO 410 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:33:19','2026-02-15 23:53:25','PROD-16',0,NULL,NULL),(17,11,2,'Filtro de Óleo JFO OH01 ( verificar preço )','Óleo',NULL,5,2,10.00,32.00,'2026-02-13 14:34:22','2026-02-15 23:53:25','PROD-17',0,NULL,NULL),(18,11,2,'Filtro de Óleo JFO OH00 ( verificar preço )','Óleo',NULL,4,2,10.00,32.00,'2026-02-13 14:34:58','2026-02-15 23:53:25','PROD-18',0,NULL,NULL);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_menu_permissions`
--

DROP TABLE IF EXISTS `role_menu_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `role_menu_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role` enum('admin','oficina','loja','pessoal') NOT NULL,
  `menu_key` varchar(50) NOT NULL,
  `can_view` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_menu_unique` (`role`,`menu_key`)
) ENGINE=InnoDB AUTO_INCREMENT=132 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_menu_permissions`
--

LOCK TABLES `role_menu_permissions` WRITE;
/*!40000 ALTER TABLE `role_menu_permissions` DISABLE KEYS */;
INSERT INTO `role_menu_permissions` VALUES (1,'admin','dashboard',1),(2,'admin','tasks',1),(3,'admin','financial',1),(4,'admin','products',1),(5,'admin','clients',1),(6,'admin','budgets',1),(7,'admin','services',1),(8,'admin','admin_users',1),(9,'oficina','dashboard',1),(10,'oficina','tasks',1),(11,'oficina','financial',1),(12,'oficina','products',1),(13,'oficina','clients',1),(14,'oficina','budgets',1),(15,'oficina','services',1),(16,'oficina','admin_users',0),(17,'loja','dashboard',1),(18,'loja','tasks',0),(19,'loja','financial',1),(20,'loja','products',1),(21,'loja','clients',1),(22,'loja','budgets',1),(23,'loja','services',0),(24,'loja','admin_users',0),(25,'pessoal','dashboard',1),(26,'pessoal','tasks',1),(27,'pessoal','financial',1),(28,'pessoal','products',0),(29,'pessoal','clients',0),(30,'pessoal','budgets',0),(31,'pessoal','services',0),(32,'pessoal','admin_users',0),(97,'admin','schedule',1),(98,'pessoal','schedule',1),(99,'','schedule',1);
/*!40000 ALTER TABLE `role_menu_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_migrations`
--

DROP TABLE IF EXISTS `schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `checksum` char(64) NOT NULL,
  `kind` enum('schema','seed') NOT NULL DEFAULT 'schema',
  `applied_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_schema_migrations_filename` (`filename`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_migrations`
--

LOCK TABLES `schema_migrations` WRITE;
/*!40000 ALTER TABLE `schema_migrations` DISABLE KEYS */;
INSERT INTO `schema_migrations` VALUES (1,'01_auth.sql','a07b197cd8f5ba8e3d05ed6de3f6dcb99bca44a472bdfa962358bce60d45ce0b','schema','2026-02-15 23:53:24'),(2,'02_tasks.sql','a41fbec110466218597cd18c6ed00a2fb39fa594fe862539656ba9b443bc4162','schema','2026-02-15 23:53:24'),(3,'02_tasks_due_date.sql','a640c53d572974541ca97099986b4832dd4dc69aec3e98d4342fe048291030d2','schema','2026-02-15 23:53:24'),(4,'03_financial.sql','4a89dbf56ca7d9189b968b375e7b254116cc962955d79645eaa83c16e6ac523a','schema','2026-02-15 23:53:24'),(5,'04_financial_payment_types.sql','6077b5435ba56953225770553f02cc028480727c56af71726c5c6ef6a5a7e333','schema','2026-02-15 23:53:24'),(6,'04_products.sql','fb2790ca52d7a81be55618ed34c4b9c6e5422f91202d2c381f4a9e7a0609198e','schema','2026-02-15 23:53:24'),(7,'05_clients.sql','e49ed71584e8dbdc35487ffdcf2a5d35292bbdeb3e4b3fe6776f7c0801d9f2ea','schema','2026-02-15 23:53:25'),(8,'07_budgets.sql','3244758f576bc2a96b2f32a6367c6abe6865129a1b4ccb85a855a76462cd8772','schema','2026-02-15 23:53:25'),(9,'07_role_menu_permissions.sql','d854ddffb65967909289abba8c9d33940effca1eb10c71e3589348922d39681d','schema','2026-02-15 23:53:25'),(10,'08_budgets_status_enum_update.sql','1f5922d6ef96a1c3111b09869f51047fe4d14491776891aad07a11a11e6d5257','schema','2026-02-15 23:53:25'),(11,'08_financial_budget_id.sql','48b3d7323cf2544bcbdf5c62bcca05573865b401ea0d82dbc1f6644e3a7ebc73','schema','2026-02-15 23:53:25'),(12,'09_budgets_split_status.sql','afed964b33439b52b2bc6e6f052907dab65446eeb2596d3b080507b309ac46ae','schema','2026-02-15 23:53:25'),(13,'10_appointments.sql','764be9841d6301091136755abee4373defe2332013b0f077ef5969b448712c85','schema','2026-02-15 23:53:25'),(14,'10_update_segment_permissions.sql','2bfb485e2c7a54918cad3104a17c7916fbcdb30d427aaf28f599e8220b68aa41','schema','2026-02-15 23:53:25'),(15,'11_update_products_retail.sql','613656a7ba8b9d340a5d2d7784a8a0236ba9ea9bb832c4d195b22aa8950ae8e3','schema','2026-02-15 23:53:25'),(16,'12_add_address_to_clients.sql','5ca0bd4fb698978592a0cadb94ddfb1da3cff6bf546156612de9e633ef3444e0','schema','2026-02-15 23:53:25'),(17,'12_financial_expenses.sql','d351283381de83a39001915aa89c0cbf77813ac5218fa81ed7ad6a601fb0af2e','schema','2026-02-15 23:53:25'),(18,'13_add_role_column.sql','c9acea9c80932212ec879d8952d8243a1ec7e18f986f7ffd1cb335b225117ca5','schema','2026-02-15 23:53:25');
/*!40000 ALTER TABLE `schema_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `services` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `mechanic` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `services_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES (1,11,'Troca de Óleo ( Sem material )','',30.00,'Aislan','2026-02-11 17:39:34','2026-02-11 17:39:34'),(2,11,'Limpeza de Bico ','',70.00,'Podium','2026-02-13 14:44:12','2026-02-13 14:44:12');
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `suppliers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
INSERT INTO `suppliers` VALUES (1,4,'Decar Peças','62985921140','2026-02-09 02:05:55'),(2,11,'Baratão','62981009246','2026-02-13 14:06:45');
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('a_fazer','fazendo','feito') DEFAULT 'a_fazer',
  `category` varchar(50) DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
INSERT INTO `tasks` VALUES (1,4,'Estudar Python Flask','Python do zero ao absoluto','feito','Estudo',NULL,'2026-02-05 12:04:23','2026-02-05 12:13:25',NULL),(2,4,'Projeto ADV - Precifex','Terminar a lista de tarefas','a_fazer','Trabalho',NULL,'2026-02-06 12:08:56','2026-02-06 12:08:56',NULL),(3,4,'Projeto Preço - Precifex','Terminar a lista de tarefas','a_fazer','Trabalho',NULL,'2026-02-07 12:09:36','2026-02-07 15:06:51',NULL),(4,4,'Estudar PHP exercícios','Básico PDO documentação etc.','a_fazer','Estudo',NULL,'2026-02-08 12:25:02','2026-02-08 15:13:43',NULL),(5,4,'Estudar SQL base diária','Estudos diários de 1h dia','feito','Estudo',NULL,'2026-02-08 12:27:51','2026-02-08 12:49:13',NULL),(6,4,'Estudar Laravel básico','Laravel 1h dia para implementar projetos modernos e escaláveis ','a_fazer','Estudo',NULL,'2026-02-08 12:32:39','2026-02-08 15:13:41',NULL),(7,4,'Estudar Cron e funções com php','1h dia para melhorar performace de aplicações','feito','Estudo',NULL,'2026-02-08 12:33:24','2026-02-08 15:06:44','2026-02-08 15:06:44'),(8,4,'Revisar documentação','Verificar erros de português','feito','Trabalho',NULL,'2026-02-01 15:28:57','2026-02-08 15:28:57','2026-02-01 15:28:57'),(9,4,'Backup do banco','Gerar dump completo','feito','Trabalho',NULL,'2026-02-02 15:28:57','2026-02-08 15:28:57','2026-02-02 15:28:57'),(10,4,'Atualizar libs','Pip upgrade','feito','Estudo',NULL,'2026-02-02 15:28:57','2026-02-08 15:28:57','2026-02-02 15:28:57'),(11,4,'Reunião cliente','Alinhamento de expectativas','feito','Trabalho',NULL,'2026-02-03 15:28:57','2026-02-08 15:28:57','2026-02-03 15:28:57'),(12,4,'Comprar café','Acabou o estoque','feito','Pessoal',NULL,'2026-02-04 15:28:57','2026-02-08 15:28:57','2026-02-04 15:28:57'),(13,4,'Estudar Flask','Ler sobre Blueprints','feito','Estudo',NULL,'2026-02-04 15:28:57','2026-02-08 15:28:57','2026-02-04 15:28:57'),(14,4,'Exercício físico','Corrida 5km','feito','Saúde',NULL,'2026-02-05 15:28:57','2026-02-08 15:28:57','2026-02-05 15:28:57'),(15,4,'Pagar contas','Luz e Internet','feito','Pessoal',NULL,'2026-02-06 15:28:57','2026-02-08 15:28:57','2026-02-06 15:28:57'),(16,4,'Deploy homologação','Subir versão v1.2','feito','Trabalho',NULL,'2026-02-07 15:28:57','2026-02-08 15:28:57','2026-02-07 15:28:57'),(17,4,'Escrever relatório','Resultados do mês','feito','Trabalho',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57','2026-02-08 15:28:57'),(18,4,'Desenvolver API','Criar endpoints REST','fazendo','Trabalho',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(19,4,'Ler livro Clean Code','Capítulo 3','fazendo','Estudo',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(20,4,'Planejar viagem','Ver passagem aérea','fazendo','Pessoal',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(21,4,'Dieta da semana','Comprar legumes','fazendo','Saúde',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(22,4,'Format PC','Instalar Windows 11','a_fazer','Pessoal',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(23,4,'Curso de React','Comprar na Udemy','a_fazer','Estudo',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(24,4,'Dentista','Marcar limpeza','a_fazer','Saúde',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(25,4,'Trocar óleo carro','Revisão 50k','a_fazer','Pessoal',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(26,4,'Atualizar LinkedIn','Adicionar projetos','a_fazer','Trabalho',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(27,4,'Organizar arquivos','Limpar área de trabalho','a_fazer','Pessoal',NULL,'2026-02-08 15:28:57','2026-02-08 15:28:57',NULL),(28,4,'Teste o sistema','Lançamentos diários','a_fazer','Trabalho',NULL,'2026-02-09 12:32:42','2026-02-09 12:32:42',NULL),(29,4,'Contratar mecânico','tarefa do dia','a_fazer','Pessoal',NULL,'2026-02-09 12:33:24','2026-02-09 12:33:24',NULL),(30,9,'Pagar energia','198','a_fazer','Pessoal',NULL,'2026-02-10 14:34:07','2026-02-10 14:34:07',NULL),(31,11,'Preciso pagar internet','Valor 108,00','feito','Trabalho',NULL,'2026-02-11 17:40:53','2026-02-11 17:41:56','2026-02-11 17:41:56'),(32,5,'Alinhar o site','Falar com o Rodrigo','feito','Trabalho',NULL,'2026-02-13 20:34:54','2026-02-13 20:35:50','2026-02-13 20:35:50');
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `role` enum('admin','oficina','loja','pessoal') NOT NULL DEFAULT 'pessoal',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Administrador','admin@sistema.com','00000000000','admin123','2026-02-08 10:58:47','admin'),(3,'Maria Sousa','rodrigoexer8@gmail.com','62985921140','123123','2026-02-08 11:14:01','pessoal'),(4,'Aline Almeida','aline@gmail.com','62998579084','123123','2026-02-08 11:20:23','admin'),(5,'Sebastião Rodrigo','rodrigoexer1@gmail.com','(62) 99857-9084','123123','2026-02-09 13:49:52','admin'),(6,'aislan@gmail.com','aislan@gmail.com','(62) 99888-6677','123123','2026-02-09 14:19:29','pessoal'),(7,'ana@gmail.com','ana@gmail.com','(66) 66666-6666','123123','2026-02-09 18:31:41','pessoal'),(8,'Edson','Edsonexer@hotmail.com','(62) 99914-0188','123456','2026-02-09 21:25:26','pessoal'),(9,'fabricio@gmail.com','fabricio@gmail.com','(62) 98592-1140','123123','2026-02-10 14:33:17','pessoal'),(10,'Emerson','emerson90_sabino@hotmail.com','','150110','2026-02-10 16:58:54','pessoal'),(11,'Aislan Podium','podium@app.com','(62) 99132-8180','123123','2026-02-11 17:32:16','oficina'),(12,'Conta Silva ','rodrigoexer2@gmail.com','(62) 99857-9084','123123','2026-02-11 22:29:58','admin');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vehicles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `plate` varchar(20) NOT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `model` varchar(100) DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `color` varchar(50) DEFAULT NULL,
  `km` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `vehicles_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES (1,4,6,'OMP7439','FIAT','STRADA',2009,NULL,109800,'2026-02-09 09:22:46','2026-02-09 09:22:46'),(2,4,1,'ODZ9929','HONDA','CIVIC',2022,NULL,18200,'2026-02-09 09:34:30','2026-02-09 12:08:14'),(3,4,3,'OGX5579','HONDA','HONDA FIT',2006,NULL,107222,'2026-02-09 10:33:54','2026-02-09 10:33:54'),(4,4,6,'ODZ9929','Fiat','Grand Siena',2009,NULL,50050,'2026-02-09 13:21:24','2026-02-09 13:21:24'),(5,4,2,'OMP7439','Chevrolet','Prisma',2018,NULL,240678,'2026-02-09 13:28:24','2026-02-09 13:29:39'),(6,11,13,'OMP-7439','FIAT','STRADA',2010,NULL,2400300,'2026-02-11 17:37:53','2026-02-11 17:37:53'),(7,11,16,'OMP-0000','Ford','EcoSporte',2010,NULL,0,'2026-02-13 14:51:20','2026-02-13 14:51:20'),(8,12,17,'AOM-3040','FIAT','FIAT STRADA',2020,NULL,5000,'2026-02-14 12:28:05','2026-02-14 12:28:05');
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-15 20:53:59
