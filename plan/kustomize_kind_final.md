# Wspólne manifesty Kubernetes i kind – plan ostateczny

Zastępuje `kustomize_kind_opus.md`, `kustomize_kind_astra.md` i `kustomize_kind_fable.md`. Nic nie zostało jeszcze zaimplementowane.

## Założenia

- Priorytet: działające, możliwie proste wdrożenie na GCP.
- Serwer koła nie jest częścią tego planu. Struktura ma tylko nie dopuścić do rozjechania się na dwie niezależne wersje – członkowie koła dostosują ją później.
- `run-locally` i E2E działają w klastrze kind. `run-locally` uruchamia też LLM, na samym CPU.
- `just dev` zostaje bez zmian.

## Struktura

```
deploy/
  base/                    # wspólne dla GCP i kind: przenośny Kubernetes, bez niczego z GKE
    kustomization.yaml
    core.yaml              # Deployment + Service
    core-worker.yaml
    core-migrations.yaml   # Job
    web.yaml               # Deployment + Service
    postgres.yaml          # Deployment + Service + PVC
    config.env             # wspólna konfiguracja → configMapGenerator
  overlays/
    gcp/
      kustomization.yaml   # base + łatki GKE + nadpisane klucze konfiguracji
      patches/             # wolumen CSI, serviceAccountName, spot, NodePort + BackendConfig, embedding-batch dla workera
      rbac.yaml
      secrets.yaml         # SecretProviderClass
      ingress.yaml         # ManagedCertificate, FrontendConfig, BackendConfig, Ingress – bez zmian
    local/
      kustomization.yaml   # base + poniższe + testowy Secret (secretGenerator)
      gateway.yaml         # obecny nginx jako Deployment + Service NodePort
      nginx.conf
      rustfs.yaml
      embedding.yaml
      extraction.yaml
      llm.yaml
    e2e/
      kustomization.yaml   # ../local, replicas: 0 dla extraction i llm, Job seeda
      core-e2e-seed.yaml
  kind/
    cluster.yaml           # mapowanie portów 8080 i 9000, katalog modeli LLM
  gcp/                     # zostają pliki infrastruktury: bucket-cors.json, cleanup policy, secrets/
```

Trzy środowiska, cztery kustomizacje. Bez Components, bez Helma, bez kontrolera ingress w kind.

### `base/`

- Treść z obecnych manifestów `deploy/gcp/` (sondy, `securityContext`, requests/limits), po wyjęciu wszystkiego, co specyficzne dla GKE.
- **Sekrety**: wolumen `secrets-store` ze zwykłego `Secret` w `/mnt/secrets-store`; klucze = nazwy plików (`RELATIONAL_DB_PASSWORD`, `APP_JWT_SECRET_KEY`, `OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`). Żadnych sekretów przez env. Kod ustawień bez zmian.
- **Konfiguracja**: `configMapGenerator` z sufiksem hasha i domyślnymi adresami usług w klastrze (`http://embedding:8080` itd.). Zmiana konfiguracji sama wymusza rollout.
- **Obrazy**: nazwy logiczne `prawobiorca/core` i `prawobiorca/web`, bez rejestru i taga; zawsze podstawia je skrypt. `latest` znika, a z nim wyjątki checkov `CKV_K8S_14`/`43`.
- **Tożsamość zasobów**: nazwy, etykiety `app`/`component` i PVC `pg-data` bez zmian. Bez `commonLabels` i `namePrefix` – selektory są niezmienne, a nowa nazwa PVC to pusty wolumen.
- **Postgres**: `pgvector:0.8.4-pg18-trixie`; overlay `gcp` przypina `0.8.2` jedną linią `images:` do czasu osobnej aktualizacji.

### `overlays/gcp`

- Łatki celowane selektorem (`target: kind`), nie kopiowane dla każdego zasobu: podmiana wolumenu `secrets-store` na CSI, `serviceAccountName`, `nodeSelector` spot.
- `configMapGenerator` z `behavior: merge`: URL-e Cloud Run/Vertex/GCS, `APP_COOKIE_SECURE`, limit kosztów LLM.
- Wynik renderowania ma być semantycznie równy obecnemu `deploy/gcp/*.yaml`.

### `overlays/local`

- **Bramka**: obecny nginx z `nginx-config.yaml` jako `Deployment` + `Service` typu NodePort, wystawiony na `localhost:8080`. Trasy bez zmian (`/api`, `/docs`, `/openapi.json`, `/`). Wdrażana razem z aplikacją, bo nginx nie wystartuje bez Serwisów `core` i `web`.
- **RustFS**: NodePort wystawiony na `localhost:9000`, jak dziś; dane dostępowe z tego samego `Secret` co aplikacja; obraz przypięty zamiast `latest`.
- **Embedding, extraction**: `Deployment` + `Service`, z sondą gotowości.
- **LLM**: OVMS w wersji CPU (`--target_device=CPU`, bez `privileged` i `/dev/dri`), obraz pobierany przez węzeł z rejestru. Modele w katalogu hosta podmontowanym do węzła kind, więc `run-locally-reset` nie kasuje pobranego modelu. Wdrożenie nie czeka na gotowość LLM – pierwsze pobranie modelu trwa długo.
- Porty 5432 i 8081–8083 nie są mapowane na hosta; w razie potrzeby `kubectl port-forward`.

### `overlays/e2e`

`resources: ../local`, do tego `replicas: 0` dla `extraction` i `llm` oraz Job seeda. Worker działa w E2E (ten sam obraz, a rollout sprawdza jego start). Seed: Job z obrazu `core`; skrypt i jeden plik danych (ok. 14 KB) w ConfigMapie generowanej z plików w `apps/core`.

## Skrypt wdrożenia

`scripts/deploy.py <env> --image core=<ref> --image web=<ref>` – jeden dla GCP, `local` i `e2e`.

1. **Jeden render**: tymczasowa kustomizacja (overlay + `images:`), `kubectl kustomize` raz do pliku. Repo nie jest modyfikowane, nazwy z hashem są spójne między etapami.
2. **Etapy z tego samego pliku**, wybierane etykietą fazy:
   - konfiguracja i zależności (wszystko bez etykiety fazy) → czekanie na rollout, z pominięciem LLM;
   - Joby po kolei: migracje, w `e2e` także seed → usunięcie starego Joba, apply, czekanie na sukces lub porażkę;
   - aplikacja (`core`, `core-worker`, `web`, bramka) → czekanie na rollout.
3. **Przy błędzie**: stan podów, zdarzenia, logi; kod wyjścia różny od zera.
4. **Bezpiecznik kontekstu**: `local` tylko na `kind-prawobiorca`, `e2e` tylko na `kind-prawobiorca-e2e`, `gcp` wymaga jawnego `--context`.

`cd.yml` i ręczne wdrożenie używają tego samego skryptu. CD zaczyna więc wdrażać także konfigurację, Ingress i Postgresa; `sed` i `deploy_app.sh` znikają.

## Lokalnie: klaster, obrazy, polecenia

Przygotowanie klastra to osobny krok w `scripts/local/`, przed skryptem wdrożenia:

1. Utworzenie klastra kind, jeśli nie istnieje (`KIND_EXPERIMENTAL_PROVIDER=podman`).
2. `podman build` dla każdego obrazu, zawsze – cache warstw zastępuje obecną heurystykę czasów modyfikacji (pomija ona `nginx.conf`, `index.html` i `vite.config.ts`).
3. Tag = skrót ID obrazu; do kind ładowane są tylko obrazy, których węzeł jeszcze nie ma (`podman save` + `kind load image-archive`).
4. `deploy.py local` z tymi tagami.

| Polecenie | Zachowanie |
| --- | --- |
| `run-locally` | Klaster `prawobiorca` (tworzony, jeśli brak), obrazy, wdrożenie z LLM |
| `run-locally-down` | Skaluje workloady do zera; klaster i dane zostają |
| `run-locally-reset` | `kind delete cluster`; kasuje bazę i storage, zostawia modele LLM |
| `run-e2e-env` | Osobny klaster `prawobiorca-e2e`; kończy dzisiejsze współdzielenie danych z `run-locally` |
| `run-e2e-env-down` | `kind delete cluster --name prawobiorca-e2e` |

Oba klastry używają portów 8080 i 9000, więc działa jeden naraz – skrypt ma to zgłaszać czytelnym błędem. Danych z obecnych wolumenów Podmana nie przenosić (baza odtwarzalna przez `just init-db`); pobrany model można jednorazowo skopiować z wolumenu `llm-model`.

## CI/CD

- **`e2e.yml`, `dast.yml`**: kind na Dockerze (kind i kubectl są na runnerach `ubuntu-latest`), `kind load docker-image` zamiast `docker save | podman load`. Embedding węzeł pobiera sam z GHCR, przypięty digestem. Logi przy błędzie ze skryptu wdrożenia.
- **`cd.yml`**: budowanie jak dziś, potem `deploy.py gcp` z tagami SHA; grupa `concurrency`, żeby dwa wdrożenia nie szły równolegle.
- **`ci.yml`**: render wszystkich trzech overlayów (wykrywa zepsute łatki), checkov na wyrenderowanym `gcp`, filtr ścieżek `deploy/**`. Ustawienia bezpieczeństwa `core`, workera, `web`, migracji i Postgresa są wspólne z definicji, więc uwaga „keep their security settings aligned” znika.

## Etapy

### Etap 0 – sprawdzenie kind na tym komputerze

Niezweryfikowane: Podman 4.9.3 rootless, cgroup v2, delegowane kontrolery `cpu memory pids`. Do sprawdzenia przed etapem 2:

1. `kind create cluster` z mapowaniem portów, `kind load image-archive`, restart węzła.
2. Zapis modelu przez pod LLM do katalogu hosta (uprawnienia w rootless).
3. LLM na CPU: zużycie pamięci (model 35B int4 to ok. 20 GB przy 31 GB RAM) i czas odpowiedzi. Jeśli za wolno lub za ciężko, zmiana modelu to dwie linie w `overlays/local`.

Jeśli rootless nie zadziała: kind na Dockerze lub rootful. Plan się nie zmienia.

### Etap 1 – `base/`, overlay `gcp`, skrypt, CD

1. `deploy/base` i `deploy/overlays/gcp`.
2. Dowód równoważności: `kubectl diff` wyrenderowanego overlayu względem klastra pokazuje tylko nazwę ConfigMapy z hashem i tagi obrazów.
3. `scripts/deploy.py`; przepięcie `cd.yml`; usunięcie `sed` i `deploy_app.sh`.
4. Sprawdzenie, czy rola `container.developer` konta `prawobiorca-deployer` wystarcza do zasobów, których CD dziś nie dotyka (Ingress, ManagedCertificate, BackendConfig, SecretProviderClass, ServiceAccount).
5. `just check-deployment` i `ci.yml` na renderze.
6. Usunięcie `deploy/gcp/*.yaml`; aktualizacja `docs/ci_cd.md`.

`deploy/local` i `podman kube play` zostają do końca etapu 2.

Kryterium: wydanie przechodzi nową ścieżką, zmiana konfiguracji sama restartuje pody, PVC i dane nietknięte. Po pierwszym wdrożeniu ręcznie usunąć starą ConfigMapę `core-config`.

### Etap 2 – `local` i `e2e` na kind

1. `deploy/overlays/local`, `deploy/overlays/e2e`, `deploy/kind/cluster.yaml`.
2. Nowe `scripts/local` i polecenia `just` z tabeli.
3. `e2e.yml` i `dast.yml` na kind.
4. Usunięcie `deploy/local` i starych skryptów.
5. Dokumentacja: `architecture.md` (sekcja `deploy/`), `ci_cd.md`, `tests/e2e.md`, README, wymagane narzędzia (kind, kubectl).

Kryterium: E2E i DAST przechodzą na kind; `run-locally` uruchamia całość z LLM; `run-locally-down` zachowuje dane.

### Etap 3 – opcjonalnie

- Te same obrazy z E2E do wdrożenia: job E2E zapisuje obrazy jako artefakt, job wdrożenia je wypycha i wdraża po digeście, bez drugiego budowania.
- pgvector na produkcji do `0.8.4` (`ALTER EXTENSION vector UPDATE`) i usunięcie przypięcia w overlayu `gcp`.

## Serwer koła – co ten plan zostawia

Wdrożenie na zwykłym Kubernetesie to nowy overlay nad `base/`, korzystający z definicji z `overlays/local` (RustFS, embedding, extraction, LLM), z prawdziwym `Secret`, domeną i własnym routingiem. `base/` nie wymaga przy tym zmian, bo nie zawiera niczego z GKE. Przeniesienie wspólnych plików z `overlays/local` do osobnego katalogu jest wtedy zmianą mechaniczną.

## Wpływ na czas

Szacunki, bez pomiarów.

- **CI na PR-ach**: render trzech overlayów, sekundy.
- **E2E**: dochodzi start klastra (ok. 30–60 s), odpada transfer Docker → Podman.
- **Lokalnie**: pierwsze `run-locally` wyraźnie dłuższe – obraz węzła ok. 1 GB i załadowanie do kind ok. 4,5 GB obrazów (extraction 3 GB, embedding 1,1 GB), które zajmą też drugie tyle miejsca na dysku. Kolejne uruchomienia ładują tylko zmienione obrazy.
