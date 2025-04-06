TYPE=TRIGGERS
triggers='CREATE DEFINER=`root`@`localhost` TRIGGER set_default_cancelled_at\nBEFORE INSERT ON magiclinks\nFOR EACH ROW\nBEGIN\n    IF NEW.cancelled_at IS NULL THEN\n        SET NEW.cancelled_at = TIMESTAMPADD(HOUR, 48, NOW());\n    END IF;\nEND'
sql_modes=1411383296
definers='root@localhost'
client_cs_names='utf8mb3'
connection_cl_names='utf8mb3_uca1400_ai_ci'
db_cl_names='utf8mb4_uca1400_ai_ci'
created=1743936254539474
