# Documentação Técnica e Queries - Portal de Tickets DS

Este documento contém a estrutura das tabelas utilizadas no Supabase para o funcionamento do Portal de Tickets da Digital Solutions.

## 1. Tabela de Utilizadores
```sql
CREATE TABLE IF NOT EXISTS utilizadores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL DEFAULT 'ds2026',
    nome TEXT NOT NULL,
    plataforma TEXT NOT NULL CHECK (plataforma IN ('ticket', 'gestao', 'ambas')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tickets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username_cliente TEXT NOT NULL,
    topico TEXT NOT NULL,
    assunto TEXT NOT NULL,
    mensagem VARCHAR(500) NOT NULL,
    email_cc TEXT,
    estado TEXT NOT NULL DEFAULT 'Aberto' CHECK (estado IN ('Aberto', 'Resolvido')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
