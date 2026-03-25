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
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-15 19:16:39
