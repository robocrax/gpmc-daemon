# System Architecture

                                  +------------------------------------+
                                  |        Container Environment       |
                                  |                                    |
  Web GUI Interface ------------->|  FastAPI Backend (Port 8080)       |
  (Dashboard, Accounts, Logs)     |   └─ SQLModel/SQLite (DB Storage)  |
                                  |   └─ Background Task Runner        |
                                  |        │                           |
  Syncthing Daemon (8384) <───────┼────────┴──> Syncthing REST API     |
  (Auto-accepts shared folders)   |               └─ Folder Auto-Sync  |
                                  |                       │            |
  GPMC CLI Engine <───────────────┼───────────────────────┘            |
  (Cycles through account dirs)   |          Files in /sync/acct_<ID>  |
                                  +------------------------------------+
                                             │               │
                                  ./data Volume        ./media Volume


                                  
