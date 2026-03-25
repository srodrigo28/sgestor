-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 76.13.225.77    Database: flask_crud
-- ------------------------------------------------------
-- Server version	5.5.5-10.11.14-MariaDB-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `budget_items`
--

DROP TABLE IF EXISTS `budget_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `budgets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `client_id` int(11) NOT NULL,
  `vehicle_id` int(11) DEFAULT NULL,
  `vehicle_km` int(11) DEFAULT NULL,
  `status` enum('draft','sent','approved','rejected','completed') DEFAULT 'draft',
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
INSERT INTO `budgets` VALUES (1,4,6,1,109800,'approved',420.00,0.00,'','2026-02-16','2026-02-09 09:22:46','2026-02-09 12:17:51'),(2,4,1,2,18200,'approved',540.00,0.00,'O cliente comprou as peças por fora','2026-02-16','2026-02-06 09:34:30','2026-02-06 09:34:30'),(3,4,3,3,107222,'approved',934.00,0.00,'','2026-02-16','2026-02-05 10:33:54','2026-02-09 13:25:30'),(4,4,1,2,50059,'approved',80.00,0.00,'O cliente troce o óleo','2026-02-16','2026-02-09 10:40:58','2026-02-09 12:04:02'),(5,4,6,4,50050,'approved',490.00,0.00,'','2026-02-16','2026-02-09 13:21:24','2026-02-09 13:21:24'),(6,4,2,5,140367,'approved',580.00,0.00,'','2026-02-16','2026-02-09 13:28:24','2026-02-09 13:28:24'),(7,4,2,5,240678,'sent',475.00,0.00,'','2026-02-16','2026-02-09 13:29:39','2026-02-09 13:29:39'),(8,11,13,6,2400300,'approved',100.00,0.00,'','2026-02-18','2026-02-11 17:37:53','2026-02-11 17:37:53'),(9,11,16,7,0,'approved',65.00,0.00,'','2026-02-20','2026-02-13 14:51:20','2026-02-13 14:54:14'),(10,12,17,8,5000,'approved',20.00,0.00,'','2026-02-21','2026-02-14 12:28:05','2026-02-14 12:28:05');
/*!40000 ALTER TABLE `budgets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
INSERT INTO `clients` VALUES (1,4,'João da Bezerra','(11) 99999-1234','(11) 3333-0000','123.456.789-00','Varejo','2026-02-09 02:44:10','2026-02-09 03:00:17'),(2,4,'Maria Oliveira','(21) 98888-5555',NULL,'987.654.321-99','Serviços','2026-02-09 02:44:10','2026-02-09 02:57:30'),(3,4,'Tech Solutions Ltda','(31) 97777-8888','(31) 3222-1111','12.345.678/0001-90','Atacado','2026-02-09 02:44:10','2026-01-09 02:57:48'),(4,1,'Padaria do Joaquim','(11) 95555-4444',NULL,'11.222.333/0001-55','Varejo','2026-02-09 02:44:10','2026-02-09 02:44:10'),(6,4,'Beatriz Silva','(62) 62626-2626','(62) 62626-2626','111.111.111-11','Tiradentes','2026-02-09 02:58:42','2026-02-09 02:58:42'),(7,1,'João da Silva','(11) 99999-1234','(11) 3333-0000','123.456.789-00','Varejo','2026-02-09 09:08:04','2026-02-09 09:08:04'),(8,1,'Maria Oliveira','(21) 98888-5555',NULL,'987.654.321-99','Serviços','2026-02-09 09:08:04','2026-02-09 09:08:04'),(9,1,'Tech Solutions Ltda','(31) 97777-8888','(31) 3222-1111','12.345.678/0001-90','Atacado','2026-02-09 09:08:04','2026-02-09 09:08:04'),(10,1,'Padaria do Joaquim','(11) 95555-4444',NULL,'11.222.333/0001-55','Varejo','2026-02-09 09:08:04','2026-02-09 09:08:04'),(11,1,'Consultoria ABC','(41) 96666-7777',NULL,'55.666.777/0001-88','Serviços','2026-02-09 09:08:04','2026-02-09 09:08:04'),(12,4,'Cristiane','(62) 99998-8888','(98) 66664-4444','222.222.222-22','Garavelo','2026-02-09 13:44:05','2026-02-09 13:44:05'),(13,11,'Sebastião Rodrigo','(62) 99857-9084','(62) 99857-9084','010.460.381-99','Buriti Sereno','2026-02-11 17:36:26','2026-02-11 17:36:26'),(14,11,'Construservice','(62) 99999-9999','(62) 88888-8888','77.777.777/7777-77','Jardim Novo Mundo','2026-02-12 22:45:46','2026-02-12 22:46:04'),(15,11,'Mazza Fashion','(62) 99999-9999','(62) 88888-8888','99.999.999/9999-99','Setor Jaó','2026-02-12 22:47:03','2026-02-12 22:47:03'),(16,11,'Viviane EcoSporte','(62) 99423-0809','(62) 99423-0809','777.777.777-77','Não consta','2026-02-13 14:47:29','2026-02-13 14:47:29'),(17,12,'Construservice',NULL,NULL,NULL,NULL,'2026-02-14 12:28:05','2026-02-14 12:28:05');
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `financial_income`
--

DROP TABLE IF EXISTS `financial_income`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
INSERT INTO `financial_income` VALUES (11,4,NULL,'Salário Fevereiro',5000.00,'salario mensal','transferência','2026-02-05','2026-02-08 17:30:43'),(12,4,NULL,'Projeto Extra',1500.00,'serviço','pix','2026-02-02','2026-02-08 17:30:43'),(16,4,NULL,'Contrato CS',1000.00,'contrato','pix','2026-02-15','2026-02-08 17:52:31'),(20,4,4,'Orçamento #4 - João da Bezerra',80.00,'serviço','cartao credito','2026-02-09','2026-02-09 12:27:49'),(21,4,1,'Orçamento #1 - Beatriz Silva',420.00,'serviço','dinheiro','2026-02-09','2026-02-09 12:28:33'),(22,4,3,'Orçamento #3 - Tech Solutions Ltda',934.00,'serviço','pix','2026-02-09','2026-02-09 12:28:49'),(23,4,5,'Orçamento #5 - Beatriz Silva',490.00,'serviço','pix','2026-02-09','2026-02-09 13:21:34'),(24,11,8,'Orçamento #8 - Sebastião Rodrigo',100.00,'serviço','dinheiro','2026-02-11','2026-02-11 17:38:11'),(33,11,9,'Orçamento #9 - Viviane EcoSporte ( aguardando pag )',65.00,'serviço','pix','2026-01-30','2026-02-13 14:54:14');
/*!40000 ALTER TABLE `financial_income` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `supplier_id` (`supplier_id`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `products_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (2,4,1,'Kit velas','Injeção Eletrônica',NULL,7,2,290.00,340.00,'2026-02-09 02:14:56','2026-02-09 02:18:09'),(3,4,1,'Óleo 5w30','Óleo',NULL,10,2,20.00,30.00,'2026-02-09 13:15:07',NULL),(4,4,1,'Junta de cabeçote GOL','GOL',NULL,10,3,75.00,95.00,'2026-02-09 13:16:34',NULL),(6,11,2,'Filtro de Óleo WO 140 ( verificar preço )','Óleo',NULL,2,2,10.00,32.00,'2026-02-13 14:23:51',NULL),(7,11,2,'Filtro de Óleo WO 460 ( verificar preço )','Óleo',NULL,2,2,10.00,32.00,'2026-02-13 14:25:18',NULL),(9,11,2,'Filtro de Óleo WO 346 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:26:01',NULL),(10,11,NULL,'Filtro de Óleo WO 240 ( verificar o preço )','',NULL,3,2,10.00,32.00,'2026-02-13 14:27:00','2026-02-13 14:27:37'),(11,11,2,'Filtro de Óleo WO 120 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:29:04',NULL),(12,11,2,'Filtro de Óleo WO 340( verificar preço )','Óleo',NULL,4,2,10.00,32.00,'2026-02-13 14:29:46',NULL),(13,11,2,'Filtro de Óleo WO 130 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:30:20',NULL),(14,11,2,'Filtro de Óleo WO 130 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:31:07',NULL),(15,11,2,'Filtro de Óleo JFO 211 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:32:29',NULL),(16,11,2,'Filtro de Óleo JFO 410 ( verificar preço )','Óleo',NULL,3,2,10.00,32.00,'2026-02-13 14:33:19',NULL),(17,11,2,'Filtro de Óleo JFO OH01 ( verificar preço )','Óleo',NULL,5,2,10.00,32.00,'2026-02-13 14:34:22',NULL),(18,11,2,'Filtro de Óleo JFO OH00 ( verificar preço )','Óleo',NULL,4,2,10.00,32.00,'2026-02-13 14:34:58',NULL);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_menu_permissions`
--

DROP TABLE IF EXISTS `role_menu_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_menu_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role` enum('admin','oficina','loja','pessoal') NOT NULL,
  `menu_key` varchar(50) NOT NULL,
  `can_view` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_menu_unique` (`role`,`menu_key`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_menu_permissions`
--

LOCK TABLES `role_menu_permissions` WRITE;
/*!40000 ALTER TABLE `role_menu_permissions` DISABLE KEYS */;
INSERT INTO `role_menu_permissions` VALUES (1,'admin','dashboard',1),(2,'admin','tasks',1),(3,'admin','financial',1),(4,'admin','products',1),(5,'admin','clients',1),(6,'admin','budgets',1),(7,'admin','services',1),(8,'admin','admin_users',1),(9,'oficina','dashboard',1),(10,'oficina','tasks',1),(11,'oficina','financial',1),(12,'oficina','products',1),(13,'oficina','clients',1),(14,'oficina','budgets',1),(15,'oficina','services',1),(16,'oficina','admin_users',0),(17,'loja','dashboard',1),(18,'loja','tasks',1),(19,'loja','financial',1),(20,'loja','products',1),(21,'loja','clients',1),(22,'loja','budgets',1),(23,'loja','services',1),(24,'loja','admin_users',0),(25,'pessoal','dashboard',1),(26,'pessoal','tasks',1),(27,'pessoal','financial',1),(28,'pessoal','products',0),(29,'pessoal','clients',0),(30,'pessoal','budgets',0),(31,'pessoal','services',0),(32,'pessoal','admin_users',0);
/*!40000 ALTER TABLE `role_menu_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Administrador','admin@sistema.com','00000000000','admin123','2026-02-08 10:58:47','pessoal'),(3,'Maria Sousa','rodrigoexer8@gmail.com','62985921140','123123','2026-02-08 11:14:01','pessoal'),(4,'Aline Almeida','aline@gmail.com','62998579084','123123','2026-02-08 11:20:23','admin'),(5,'Sebastião Rodrigo','rodrigoexer1@gmail.com','(62) 99857-9084','123123','2026-02-09 13:49:52','admin'),(6,'aislan@gmail.com','aislan@gmail.com','(62) 99888-6677','123123','2026-02-09 14:19:29','pessoal'),(7,'ana@gmail.com','ana@gmail.com','(66) 66666-6666','123123','2026-02-09 18:31:41','pessoal'),(8,'Edson','Edsonexer@hotmail.com','(62) 99914-0188','123456','2026-02-09 21:25:26','pessoal'),(9,'fabricio@gmail.com','fabricio@gmail.com','(62) 98592-1140','123123','2026-02-10 14:33:17','pessoal'),(10,'Emerson','emerson90_sabino@hotmail.com','','150110','2026-02-10 16:58:54','pessoal'),(11,'Aislan Podium','podium@app.com','(62) 99132-8180','123123','2026-02-11 17:32:16','oficina'),(12,'Conta Silva ','rodrigoexer2@gmail.com','(62) 99857-9084','123123','2026-02-11 22:29:58','admin');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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

--
-- Dumping events for database 'flask_crud'
--

--
-- Dumping routines for database 'flask_crud'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-15 20:12:50
