# Rate limiting i tańsze wystawienie Prawobiorcy — podsumowanie rozmowy

Data: 2026-11-16.

Status: analiza wariantów i rekomendacja do dalszego dopracowania. Rozmowa nie zakończyła się zleceniem wdrożenia. Nie zmieniono infrastruktury GCP ani konfiguracji aplikacji; wykonano odczyty repozytorium, dokumentacji dostawców i wybranych zasobów GCP.

## 1. Cel i ustalone potrzeby

- Ograniczyć nadużycia API oraz chronić kosztowne operacje AI.
- Uniknąć kolejnej stałej opłaty rzędu 10 USD miesięcznie za Cloud Armor.
- Sprawdzić możliwość zmniejszenia obecnych kosztów GKE Ingress / load balancera.
- Zachować możliwość uruchamiania wielu replik `core`.
- Zachować przenośność na serwer on-premise koła naukowego.
- Nie utrudnić przyszłego dodania SSR dla części aplikacji.

Użytkownik potwierdził, że limity wykorzystania AI mają być egzekwowane w backendzie. Wybór dostawcy wejścia do aplikacji i szczegółowej konfiguracji rate limitingu pozostaje propozycją, a nie wdrożoną decyzją.

## 2. Stan projektu sprawdzony podczas rozmowy

### Aplikacja i infrastruktura

- Backend `core` korzysta z FastAPI; zadania w tle wykonuje worker Taskiq z kolejką opartą na PostgreSQL.
- Frontend to Vue + Vite, obecnie jako SPA. Obraz `web` zawiera nginx serwujący zbudowane pliki statyczne.
- Manifesty bazowe przewidują po jednej replice `core` i `web`.
- Skrypt inicjalizacji GCP tworzy klaster GKE Autopilot.
- GCP overlay zawiera Ingress klasy `gce`, `ManagedCertificate`, przekierowanie na HTTPS przez `FrontendConfig` oraz `BackendConfig`.
- Dla `www.prawobiorca.pl` ścieżka `/api` trafia obecnie bezpośrednio do `core`, a `/` do `web`. API omija nginx frontendu.
- `core` i `web` otrzymują w GCP ten sam `BackendConfig` oraz typ usługi `NodePort`.
- Nginx frontendu przekierowuje `prawobiorca.pl` na `www.prawobiorca.pl`.
- Usługi Cloud Run `extraction`, `embedding` i `embedding-batch` są wdrażane z `--ingress=internal`. Ich limity instancji i współbieżności nie zastępują limitów użytkowników API.
- Przesyłanie plików odbywa się bezpośrednio między przeglądarką a storage przez podpisane URL-e. Nie przechodzi przez `core`.

Istotne pliki:

- [Ingress GCP](../deploy/overlays/gcp/ingress.yaml)
- [Patch usług GCP](../deploy/overlays/gcp/patches/gke-backend.yaml)
- [Nginx frontendu](../apps/web/nginx.conf)
- [Obraz frontendu](../apps/web/Containerfile)
- [Deployment web](../deploy/base/web.yaml)
- [Deployment core](../deploy/base/core.yaml)
- [Skrypt inicjalizacji GCP](../scripts/cloud/cloud_inith.sh)

### Lokalne wdrożenie i on-premise

- `deploy/base` jest wspólną, przenośną bazą Kubernetes.
- Lokalne wdrożenie i E2E używają kind oraz dodatkowego nginx gatewaya.
- Gateway kieruje `/api` bezpośrednio do `core`, `/` do `web`, a osobno obsługuje dokumentację API i `/storage/`.
- Dokumentacja przewiduje wdrożenie na innym klastrze jako nowy overlay nad `base`, z wykorzystaniem definicji usług obliczeniowych i RustFS.
- Nie znaleziono gotowego overlayu produkcyjnego dla serwera koła. `scripts/deploy.py` obsługuje obecnie tylko `gcp`, `local` i `e2e`.
- Historyczny plan w `plan/kustomize_kind_final.md` wprost pozostawia dostosowanie serwera koła na później. Aktualne manifesty są ważniejszym źródłem stanu implementacji niż ten plan.

Nie zweryfikowano faktycznej konfiguracji sieci, proxy ani klastra na serwerze koła.

## 3. Dwie różne warstwy limitów

### Ochrona wejścia HTTP

Obejmuje ograniczanie intensywności ruchu, najczęściej po IP i ścieżce, zanim zostanie wykonana kosztowna praca aplikacji. Może działać w Cloud Armor, Cloudflare, nginx albo w FastAPI.

Limity IP trzeba dobierać z uwzględnieniem wielu studentów korzystających ze wspólnego adresu uczelni lub akademika.

### Limity wykorzystania AI

Powinny działać w backendzie na podstawie zweryfikowanej tożsamości użytkownika, niezależnie od drogi wejścia do aplikacji. Proponowany zakres:

- liczba generowań w ciągu doby;
- liczba aktywnych i oczekujących zadań;
- limity dokumentów, ich rozmiaru i ponowień przetwarzania;
- atomowe sprawdzanie i rezerwowanie limitu przed zleceniem zadania;
- ustalone zasady rozliczania błędów i ponowień.

Istniejący PostgreSQL jest rozsądnym pierwszym miejscem dla tych liczników. Redis/Memorystore można rozważyć później dla dużej liczby częstych operacji. Sprawdzenie i aktualizacja limitu muszą być odporne na równoległe żądania do różnych replik `core`.

## 4. Rozważane rozwiązania rate limitingu

### Cloud Armor

Pierwszą rekomendacją było dołączenie polityki Cloud Armor do istniejącego load balancera przez `BackendConfig.spec.securityPolicy.name`. Nie wymagałoby to dodatkowego load balancera.

Zalety:

- blokowanie ruchu przed aplikacją;
- limity po IP i warunkach żądania;
- tryb preview do obserwacji przed włączeniem blokowania;
- akcje throttle i czasowego bana.

Ograniczenia:

- limity są przybliżone, nie nadają się do ścisłego rozliczania AI;
- szczegółowa reguła o wyższym priorytecie może zakończyć ocenę; ogólny limit niżej nie nakłada się automatycznie;
- wskazane byłoby rozdzielenie konfiguracji dla API i statycznego frontendu.

Podany koszt katalogowy Standard: około 5 USD/miesiąc za politykę, 1 USD/miesiąc za regułę i 0,75 USD za milion żądań dla polityki globalnej. Przykład jednej polityki, pięciu reguł łącznie i miliona żądań: około 10,75 USD/miesiąc, poza load balancingiem i logowaniem.

Użytkownik uznał ten dodatkowy koszt za zbyt wysoki, dlatego dalsza analiza skupiła się na tańszych rozwiązaniach.

### Limiter w FastAPI

Liczniki w pamięci procesu są prostym, szybkim wariantem bez nowej usługi. Nadają się do podstawowego ograniczania nadużyć przy małym wdrożeniu, ale:

- restart zeruje liczniki;
- każdy proces i replika mają osobne liczniki;
- trzeba ograniczyć rozmiar przechowywanego stanu;
- ruch i tak dociera do aplikacji.

W rozmowie doprecyzowano, że takie rozwiązanie jest akceptowalnym kompromisem na początek, choć nie nadaje się do trwałych budżetów AI. Alternatywą są współdzielone liczniki w PostgreSQL kosztem dodatkowych zapisów do bazy.

### API Gateway / Cloud Endpoints

Oceniono je jako słabo dopasowane do obecnego problemu. Opisany mechanizm kwot identyfikuje konsumenta przez projekt Google Cloud i klucz API, co nie odpowiada bezpośrednio użytkownikom zalogowanym w Prawobiorcy. Nie rekomendowano dodawania tej warstwy tylko dla rate limitingu.

## 5. Wykorzystanie istniejącego nginx frontendu

Rozważono zmianę przepływu:

```text
Obecnie:
GKE Ingress ── /api → core
            └─ /    → web/nginx → pliki statyczne

Wariant z limiterem nginx:
GKE Ingress → web/nginx ── /api → limiter → core
                       └─ /    → pliki statyczne
```

Wymagałoby to:

1. Skierowania `/api` w GCP Ingress do `web`.
2. Dodania w nginx proxy do `core:8000`, reguł `limit_req` i odpowiedzi `429`.
3. Pozostawienia `core` jako usługi wewnętrznej i usunięcia zbędnych dróg publicznego dostępu omijających limiter.
4. Poprawnego ustalania IP klienta za zaufanym proxy.

Zachowane zostałyby obecny load balancer, HTTPS i certyfikaty GCP. Nie potrzeba nowego kontrolera ingress ani Redis. Pozostaje narzut zasobów na istniejący nginx i opłata za load balancer.

### Skalowanie

- Wiele replik `core` nie mnoży limitu nginx: żądanie jest sprawdzane przed przekazaniem do usługi Kubernetes `core`.
- Usługa Kubernetes rozdziela połączenia między dostępne pody; nie należy zakładać idealnie równego rozdziału każdego żądania przy utrzymywanych połączeniach.
- Wiele replik `web/nginx` oznacza osobne liczniki na instancję i możliwość wzrostu łącznego dopuszczonego ruchu.
- Jedna replika nginx może stać się ograniczeniem wydajności i dostępności.

### Zamiana całego GKE Ingress na kontroler NGINX

Jest możliwa, ale zwykle nadal wymaga usługi `LoadBalancer`, która tworzy płatny load balancer TCP w GCP. Dodatkowo dochodzi utrzymanie kontrolera i certyfikatów, np. przez cert-manager. Nie gwarantuje więc niższego kosztu całości.

Rozróżniono dwa projekty:

- społecznościowy `ingress-nginx` Kubernetes został wycofany w marcu 2026 i nie jest rekomendowany do nowego wdrożenia;
- NGINX Ingress Controller od F5/NGINX jest odrębnym projektem z wariantem open source.

## 6. Wpływ na on-premise

Proxy i rate limiting w zwykłym nginx nie wprowadzają zależności od GCP. Ten sam obraz aplikacji może działać za wejściem GCP albo proxy koła.

Zależne od środowiska powinny pozostać:

- adresy zaufanych proxy i sposób odczytu IP klienta;
- domeny i przekierowania;
- terminacja HTTPS i przekazywanie informacji o oryginalnym protokole;
- progi limitów;
- publiczne adresy storage.

Jeżeli limiter znajdzie się w `web`, gateway kind powinien kierować `/api` przez `web`, aby lokalne wdrożenie i E2E nie omijały nowej warstwy. Osobne trasy storage oraz dokumentacji API trzeba zachować lub świadomie przenieść.

Obecne przekierowanie domeny w `apps/web/nginx.conf` warto konfigurować przez środowisko. Nowy overlay on-premise i wpis w skrypcie deploymentu są potrzebne niezależnie od wyboru limitera. Nie należy traktować lokalnych sekretów i ustawień kind jako gotowej konfiguracji produkcyjnej.

`just dev` korzysta z proxy Vite, więc nie przechodzi automatycznie przez nginx obrazu produkcyjnego.

## 7. Wpływ przyszłego SSR

Nginx nie blokuje SSR, ale sam nie renderuje Vue na żądanie. Potrzebny będzie proces renderujący, zwykle Node.js, a nginx może nadal obsługiwać routing, pliki statyczne i limity.

```text
Wejście → nginx ── /api        → core
                ├─ strony SSR → serwer SSR → core
                └─ pliki/SPA  → pliki statyczne
```

Możliwe jest SSR tylko wybranych stron, np. publicznych regulaminów, przy pozostawieniu panelu użytkownika jako SPA.

Konsekwencje:

- trzeba ograniczać również żądania stron SSR, ponieważ pojedyncze renderowanie może wywołać kilka zapytań do API;
- SSR może komunikować się z `core` bezpośrednio wewnątrz klastra;
- limity AI nadal muszą działać w `core`;
- obecny frontend wymaga dostosowania do SSR, m.in. inicjalizacji aplikacji i routera oraz izolacji stanu sesji i klienta API między żądaniami;
- obecny współdzielony stan odświeżania sesji w kliencie Axios nie powinien być bezrefleksyjnie przenoszony do wieloużytkownikowego procesu SSR.

Jeśli SSR jest odległym pomysłem, nginx w `web` pozostaje sensownym uproszczeniem. Jeżeli jest bliskim planem, osobny gateway nginx ułatwi niezależne skalowanie renderowania i wejścia. Konfigurację routingu warto utrzymywać tak, aby dało się ją przenieść bez przepisywania reguł.

## 8. Faktycznie sprawdzone zasoby i koszty wejścia GCP

Wykonano odczyty:

```sh
gcloud compute forwarding-rules list --project=prawobiorca
gcloud compute addresses list --project=prawobiorca
dig +short NS prawobiorca.pl
```

Wyniki:

- dwie globalne reguły typu `EXTERNAL`, dla TCP 80 i 443, utworzone przez GKE Ingress;
- obie używają jednego publicznego IP;
- adres jest oznaczony jako `IN_USE` i przypisany do tych reguł;
- DNS domeny obsługują obecnie `ns1.hostido.net.pl`, `ns2.hostido.net.pl`, `ns3.hostido.net.pl`.

Według sprawdzonego cennika:

| Pozycja | Cena katalogowa |
| --- | --- |
| Pierwsze 5 globalnych reguł przekazywania, łącznie | 0,025 USD/h |
| Orientacyjny koszt przy 730 h w miesiącu | 18,25 USD |
| Publiczny IP przypisany do reguł przekazywania | Bez dodatkowej opłaty za sam adres |
| Przetwarzanie danych i transfer | Dodatkowo, zależnie od ruchu |

Nie należy mnożyć 18,25 USD przez dwie istniejące reguły. To oszacowanie katalogowe na podstawie zasobów, nie odczyt faktury. Nie sprawdzono rabatów, kredytów, podatków ani faktycznych pozycji rozliczeniowych.

## 9. Cloudflare Tunnel jako sposób usunięcia kosztu load balancera

Użytkownik zapytał o uruchomienie „poda Cloudflare”. Rozpoznano ten wariant jako Cloudflare Tunnel z procesem `cloudflared` w GKE.

```text
Użytkownik → Cloudflare → tunel → cloudflared → usługi wewnątrz klastra
```

`cloudflared` nawiązuje połączenia wychodzące do Cloudflare. Publiczne żądania są przesyłane przez istniejący tunel, więc aplikacja nie potrzebuje publicznego load balancera GCP. Tunnel jest dostępny także w planie Free.

### Koszty i wymagania

- Po migracji i usunięciu starego GKE Ingress oraz jego load balancera można wyeliminować około 18,25 USD miesięcznie podstawowej opłaty za obecne globalne reguły.
- Samo włączenie proxy Cloudflare przed starym adresem GCP nie usuwa tej opłaty.
- Dochodzą zasoby `cloudflared` rozliczane przez Autopilot. Nadal płaci się za transfer wychodzący z GCP; jeśli potrzebny jest Cloud NAT, jego koszt także należy uwzględnić.
- Nie oszacowano jeszcze oszczędności netto po dobraniu liczby replik i zasobów tunelu.
- Dla dostępności zaproponowano dwie repliki `cloudflared`.
- Typowe wdrożenie własnej domeny w planie Free wymaga obsługi DNS w Cloudflare. Rejestrator może pozostać ten sam; trzeba zachować istniejące rekordy, w tym pocztowe.
- Dochodzi zależność od Cloudflare i jego limitów połączeń oraz czasu odpowiedzi.
- Obecne zadania AI w tle i bezpośrednie transfery do storage dobrze pasują do takiego modelu.
- Tunel jest również przenośny na on-premise, w tym do sieci za NAT-em, jeśli dozwolone są wymagane połączenia wychodzące.

Migrację warto sprawdzić najpierw pod testową subdomeną, następnie przełączyć ruch produkcyjny i dopiero później usunąć stare zasoby. Zarezerwowanych adresów nie należy pozostawiać bez sprawdzenia ich dalszego wykorzystania i kosztów.

## 10. Rate limiting Cloudflare Free — ostatnie ustalenie

Cloudflare ma własny rate limiting także w planie Free. Wcześniejszą rekomendację nginx uzupełniono o możliwość użycia tej funkcji jako pierwszej warstwy ochrony.

| Możliwość | Plan Free według dokumentacji sprawdzonej w rozmowie |
| --- | --- |
| Liczba reguł | 1 na strefę domeny |
| Zliczanie | Po IP |
| Okno zliczania | 10 sekund |
| Czas blokowania | 10 sekund |
| Dopasowanie żądań | M.in. według ścieżki URL |

Przykładowy zakres jednej reguły: `/api/`, z progiem N żądań w 10 sekund z jednego IP. Konkretnego progu nie ustalono.

Jedna reguła może objąć wiele endpointów, ale przy takim ustawieniu korzystają one ze wspólnego progu i licznika per IP. Nie daje to osobnych limitów dla logowania, wyszukiwania i pozostałego API.

Regułę trzeba skonfigurować — samo uruchomienie tunelu nie ustawia limitu aplikacji. Jest egzekwowana przed GCP i nie mnoży się przez liczbę replik `core` lub `web`. Liczniki Cloudflare są jednak przybliżone i mają zakres centrum danych; nie są ścisłym globalnym licznikiem budżetu użytkownika.

### Aktualna rekomendacja

1. Cloudflare Tunnel zamiast obecnego publicznego load balancera GCP, po sprawdzeniu kosztu podów i wymagań DNS/sieci.
2. Jedna darmowa reguła Cloudflare do podstawowej ochrony API.
3. Limity AI w backendzie, ze wspólnym PostgreSQL i atomową rezerwacją wykorzystania.
4. Dodatkowe limity nginx dopiero wtedy, gdy potrzebne będą niezależne progi dla poszczególnych endpointów.

**Jeżeli jedna reguła Cloudflare wystarczy, nie trzeba kierować API przez nginx frontendu.** Tunel może kierować `/api` bezpośrednio do `core`, a pozostały ruch do `web`. W takim wariancie wcześniejsze propozycje przenoszenia API do nginx i zmiany routingu kind są opcjonalne, nie są warunkiem wdrożenia Cloudflare.

Jeżeli później limiter będzie działał także w nginx, adres klienta można ustalać na podstawie `CF-Connecting-IP`, przy zaufaniu wyłącznie do poprawnie zabezpieczonej ścieżki od `cloudflared`.

## 11. Pozostałe kwestie przed wdrożeniem

- Potwierdzenie faktycznych pozycji na rachunku GCP i oszacowanie kosztu zasobów tunelu.
- Decyzja o migracji DNS i sprawdzenie wszystkich rekordów domeny.
- Weryfikacja sieci wychodzącej klastra i ewentualnego Cloud NAT.
- Dobór jednej reguły Cloudflare i progu na podstawie rzeczywistego ruchu.
- Ustalenie, czy niezależne limity logowania i wyszukiwania są potrzebne od początku.
- Projekt limitów AI i zasad ich rezerwacji, zwalniania oraz obsługi ponowień.
- Test pod subdomeną, test logowania/cookies i odpowiedzi po przekroczeniu limitu.
- Weryfikacja dostępu do plików i przyszłych wymagań SSR.
- Przygotowanie planu przełączenia i powrotu oraz usunięcia zbędnych zasobów dopiero po weryfikacji.
- Przy wdrożeniu na serwerze koła: osobny overlay i potwierdzenie rzeczywistej konfiguracji sieci oraz HTTPS.

## 12. Źródła

Ceny i ograniczenia planów mogą się zmieniać. Poniższe źródła sprawdzono podczas rozmowy; przed implementacją należy zweryfikować parametry mające wpływ na koszt i konfigurację.

- [Cloud Armor — rate limiting](https://docs.cloud.google.com/armor/docs/rate-limiting-overview)
- [Cloud Armor — cennik](https://cloud.google.com/armor/pricing)
- [GKE — BackendConfig i Cloud Armor](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/ingress-configuration)
- [GCP — ceny sieci, adresów IP i reguł przekazywania](https://cloud.google.com/vpc/network-pricing)
- [GKE — usługi LoadBalancer](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/service-load-balancer)
- [Kubernetes — wycofanie ingress-nginx](https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/)
- [F5 NGINX Ingress Controller — polityki](https://docs.nginx.com/nginx-ingress-controller/configuration/policy-resource/policy-reference/)
- [NGINX — limit_req](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- [NGINX — realip](https://nginx.org/en/docs/http/ngx_http_realip_module.html)
- [PostgreSQL — INSERT i ON CONFLICT](https://www.postgresql.org/docs/16/sql-insert.html)
- [API Gateway — kwoty](https://docs.cloud.google.com/api-gateway/docs/quotas-overview)
- [Cloud Endpoints — model kwot](https://docs.cloud.google.com/endpoints/docs/openapi/quotas-overview)
- [Vue — SSR i izolacja stanu](https://vuejs.org/guide/scaling-up/ssr.html)
- [Vite — SSR](https://vite.dev/guide/ssr.html)
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)
- [Cloudflare Tunnel — wymagania i konfiguracja](https://developers.cloudflare.com/tunnel/get-started/)
- [Cloudflare Tunnel — Kubernetes](https://developers.cloudflare.com/tunnel/guides/kubernetes/)
- [Cloudflare — nagłówki HTTP](https://developers.cloudflare.com/fundamentals/reference/http-headers/)
- [Cloudflare — limity połączeń](https://developers.cloudflare.com/fundamentals/reference/connection-limits/)
- [Cloudflare — rate limiting i dostępność w planach](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Cloudflare — sposób zliczania żądań](https://developers.cloudflare.com/waf/rate-limiting-rules/request-rate/)
