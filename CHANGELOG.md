# CHANGELOG


## v0.1.1 (2025-05-09)

### Bug Fixes

- Refactor CD workflow to use workflow_run for CI success confirmation and streamline release
  process
  ([`6c74230`](https://github.com/fotapol/fastboosty-payment_service/commit/6c742307f0744792b410f8e56ecc45548f940105))

- Update Dockerfile and .dockerignore for improved dependency management and build efficiency
  ([`e40e26c`](https://github.com/fotapol/fastboosty-payment_service/commit/e40e26ce25a7f6947ec25016b9934f019ced7aa8))

- Update semantic release configuration for release management in pyproject.toml
  ([`8a4996c`](https://github.com/fotapol/fastboosty-payment_service/commit/8a4996cd48396688ba91dec0c1af94036dc6c9ed))


## v0.1.0 (2025-05-08)

### Bug Fixes

- Remove AUTH_SERVICE_URL from config and .env.sample
  ([`34f990f`](https://github.com/fotapol/fastboosty-payment_service/commit/34f990f6c2f3aeaf16a94a3909f402afd89ed030))

- **config**: Set default value for DOMAIN and correct Kafka config type annotations. Update
  settings for ruff
  ([`d04ac55`](https://github.com/fotapol/fastboosty-payment_service/commit/d04ac55f006f14864b38cfef5e30ee0efe17aeaf))

- **payment**: Update webhook for correct work
  ([`576249a`](https://github.com/fotapol/fastboosty-payment_service/commit/576249a191e0fc74f884afee8d88e502bb2d488b))

### Chores

- Styling code using ruff formater
  ([`c0dcfb4`](https://github.com/fotapol/fastboosty-payment_service/commit/c0dcfb42f665bcae2488a39e55a51082ba0ca17b))

### Features

- Add auth-lib dependency for authentication handling
  ([`2aafac9`](https://github.com/fotapol/fastboosty-payment_service/commit/2aafac90da79eb3f2a00ab670ce0ebcff7d3ef21))

- Add CI workflow configuration for testing and formatting checks
  ([`a497992`](https://github.com/fotapol/fastboosty-payment_service/commit/a49799232ee4b66a4a348ab76bf55019b5a7025f))

- Add Continuous Delivery workflow and update Continuous Integration workflow name
  ([`6d21190`](https://github.com/fotapol/fastboosty-payment_service/commit/6d211905a00a17b565bd184b4c5ae790ec86bd83))

- Add initial .dockerignore file to exclude Python cache
  ([`39810b8`](https://github.com/fotapol/fastboosty-payment_service/commit/39810b84011520a02bbd72859271190778b23914))

- Add python-semantic-release package. Update main.py.
  ([`d0c96c5`](https://github.com/fotapol/fastboosty-payment_service/commit/d0c96c5e8b6cf5c2b6773088520725c4bee6581f))

- Add support for feature branches in CI/CD workflows and configure semantic release settings
  ([`7fa5211`](https://github.com/fotapol/fastboosty-payment_service/commit/7fa5211109206d16939dd30a08d6d83e95e15c0e))

- Remove deprecated import of CurrentUserUUID from dependencies and add new import from new package
  ([`eb8dfcb`](https://github.com/fotapol/fastboosty-payment_service/commit/eb8dfcb7b720731d0403b9d711dc464f371d276b))

- Update CI/CD workflows
  ([`b2bdd20`](https://github.com/fotapol/fastboosty-payment_service/commit/b2bdd20090c00a69d8b3aa6356f00a37937af9bc))

- Update Python version to 3.13 in the Dockerfile for improved dependency installation. Update
  auth-lib version
  ([`21afe26`](https://github.com/fotapol/fastboosty-payment_service/commit/21afe26b662455eb568ba073e5ed15518632a14b))

- **payment**: Add Alembic configuration and migration scripts for database management
  ([`f53d6cd`](https://github.com/fotapol/fastboosty-payment_service/commit/f53d6cdd03b4a36d70d7f14a276f4a26e2ed2811))

- **payment**: Add Dockerfile and entrypoint script for payment service setup. Add routers to
  main.py.
  ([`f02c48b`](https://github.com/fotapol/fastboosty-payment_service/commit/f02c48b2453d4dfde9a2a05d006d9037aaae5ddc))

- **payment**: Add models for payment confirmation and intent request
  ([`7007f1e`](https://github.com/fotapol/fastboosty-payment_service/commit/7007f1e00997d06fdc0a5fffbe4096395742157a))

- **payment**: Add payment models and schemas for handling payment processing and events
  ([`02f77f1`](https://github.com/fotapol/fastboosty-payment_service/commit/02f77f122c14d96c05402a806c4b950bdade442d))

- **payment**: Add user authentication dependency and configure Stripe API key on startup
  ([`1b2f763`](https://github.com/fotapol/fastboosty-payment_service/commit/1b2f763e14d908959643414655975f67154fec95))

- **payment**: Implement KafkaClient for message production and handling
  ([`625f094`](https://github.com/fotapol/fastboosty-payment_service/commit/625f094cd4dd227f90152b656ddee60061dc5599))

- **payment**: Implement payment confirmation, intent creation, and Stripe webhook handling
  ([`2bb3c83`](https://github.com/fotapol/fastboosty-payment_service/commit/2bb3c83bb030c450e489a07414fb0cc6aa3e1e45))

- **payment**: Implement Stripe checkout session creation and remove deprecated payment endpoints
  ([`9ac7700`](https://github.com/fotapol/fastboosty-payment_service/commit/9ac77002534deee579599fe0a6c8256f990289a3))

- **payment**: Implement Stripe webhook handler for processing payment events and publishing to
  Kafka
  ([`c27f01b`](https://github.com/fotapol/fastboosty-payment_service/commit/c27f01ba3f70541e81ed759fe495d3715ef7c88b))

- **payment**: Initialize Kafka Producer during application startup and improve error handling
  ([`a6e2c66`](https://github.com/fotapol/fastboosty-payment_service/commit/a6e2c666885e7c560fdb6e9da0d49f7e48529ee6))

- **payment**: Initialize payment service with configuration, database setup, and basic endpoints
  ([`361cc5a`](https://github.com/fotapol/fastboosty-payment_service/commit/361cc5a32df506e000374c8e0360ecd2c0e9a0d6))

- **payment**: Refactor code structure for improved readability and maintainability
  ([`611d3c9`](https://github.com/fotapol/fastboosty-payment_service/commit/611d3c90e11dcbaa0e6aa233cf04a3b2b50985ed))

- **payment**: Remove await from Kafka producer initialization and closure
  ([`5d9b0c8`](https://github.com/fotapol/fastboosty-payment_service/commit/5d9b0c83e1c6f32fde7b546d9a9802b9acfc8476))

- **payment**: Update checkout session to use correct tier price in cents and default currency
  ([`8b23b1e`](https://github.com/fotapol/fastboosty-payment_service/commit/8b23b1ef73e17d9afc974636c32caa642eb210ec))

- **payment**: Update payment model and schemas for payment processing
  ([`20fb1a8`](https://github.com/fotapol/fastboosty-payment_service/commit/20fb1a8cf0bd20d690ec8d0a81427aa1322e10b6))

### Refactoring

- Add log message
  ([`16a7ead`](https://github.com/fotapol/fastboosty-payment_service/commit/16a7ead38136570eee55db33a406dbb1442ecc07))

- Code styling using ruff formater
  ([`d85e0a5`](https://github.com/fotapol/fastboosty-payment_service/commit/d85e0a5afb054eb53839269227134e960314c4d0))

- **payment**: Improve logging format
  ([`72d2f34`](https://github.com/fotapol/fastboosty-payment_service/commit/72d2f34b28bfdc1abec95685998a42e17301554d))
