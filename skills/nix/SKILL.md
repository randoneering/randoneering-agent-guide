---
name: nix
description: "Nix/NixOS package development, maintenance, and system configuration. Triggers: .nix, flake.nix, default.nix, nixpkgs, derivation, buildRustPackage, buildPythonPackage, NixOS modules. Covers package development, nixpkgs contributions, NixOS configuration, flakes, derivations, overlays, and troubleshooting build failures."
---

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

# Nix/NixOS Development Workflow

Comprehensive guidelines for Nix package development, nixpkgs maintenance, NixOS configuration, and build troubleshooting.

## Tool Grid

| Task | Command | Notes |
|------|---------|-------|
| Build package | `nix-build -A <attr>` | Legacy builder |
| Build with flakes | `nix build .#<package>` | Modern flake-based |
| Develop environment | `nix develop` | Enter dev shell with dependencies |
| Run package | `nix run .#<package>` | Execute from flake |
| Show derivation | `nix show-derivation` | Inspect build inputs |
| Search packages | `nix search nixpkgs <query>` | Find packages |
| Update flake inputs | `nix flake update` | Update all inputs |
| Build NixOS config | `nixos-rebuild build` | Test config without activation |
| Check syntax | `nix-instantiate --parse` | Validate Nix syntax |
| Evaluate expression | `nix-instantiate --eval` | Check attribute values |
| Format code | `nixfmt` or `alejandra` | Format Nix files |

## Critical Nix Principles

### Purity and Reproducibility
- Builds MUST be pure and reproducible
- MUST NOT access network during build phase
- MUST declare all dependencies explicitly
- Use `fetchFromGitHub`, `fetchurl`, etc. in fetchers, not in build phase
- Use `nix-hash` or `nix-prefetch-url` to get correct hashes

### Immutability
- Derivations are immutable once built
- MUST NOT modify `/nix/store` contents
- Use overlays for local modifications
- Patches go in `patches/` directory, referenced in derivation

## Package Development

### Derivation Structure

Standard derivation template:
```nix
{ lib
, stdenv
, fetchFromGitHub
, buildRustPackage  # or buildPythonPackage, buildGoModule, etc.
, pkg-config
, openssl
, ...
}:

buildRustPackage rec {
  pname = "package-name";
  version = "1.0.0";

  src = fetchFromGitHub {
    owner = "owner-name";
    repo = "repo-name";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  cargoHash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";

  nativeBuildInputs = [ pkg-config ];
  buildInputs = [ openssl ];

  meta = with lib; {
    description = "Short package description";
    homepage = "https://example.com";
    license = licenses.mit;
    maintainers = with maintainers; [ your-handle ];
    mainProgram = "executable-name";
  };
}
```

### Build Input Classification

**nativeBuildInputs**: Tools needed at build time (run on build platform)
- Examples: `pkg-config`, `cmake`, `cargo`, `rustc`, `makeWrapper`
- These execute during the build

**buildInputs**: Libraries needed at build AND runtime (target platform)
- Examples: `openssl`, `sqlite`, `postgresql`
- Linked into the final binary

**propagatedBuildInputs**: Dependencies that consumers also need
- Examples: Python/Node libraries that import other libraries
- Automatically added to dependent packages

**checkInputs**: Dependencies only for running tests
- Examples: `pytest`, `cargo-nextest`
- Only needed when `doCheck = true`

### Language-Specific Builders

#### Rust Packages
```nix
buildRustPackage rec {
  pname = "rust-app";
  version = "1.0.0";

  src = fetchFromGitHub { ... };

  cargoHash = "sha256-...";  # Use lib.fakeHash initially, update after first build

  # Optional: Lock file handling
  cargoLock = {
    lockFile = ./Cargo.lock;
    outputHashes = {
      "dependency-0.1.0" = "sha256-...";
    };
  };

  # Build-time flags
  cargoBuildFlags = [ "--all-features" ];
  
  # Skip tests if they require network/special setup
  doCheck = false;
  
  meta = { ... };
}
```

#### Python Packages
```nix
buildPythonPackage rec {
  pname = "python-pkg";
  version = "1.0.0";
  pyproject = true;  # For pyproject.toml-based projects

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-...";
  };

  build-system = [ setuptools ];  # or hatchling, poetry-core, etc.

  dependencies = [
    requests
    pydantic
  ];

  optional-dependencies = {
    dev = [ pytest black ];
  };

  pythonImportsCheck = [ "module_name" ];

  meta = { ... };
}
```

#### Node.js Packages
```nix
buildNpmPackage rec {
  pname = "node-app";
  version = "1.0.0";

  src = fetchFromGitHub { ... };

  npmDepsHash = "sha256-...";

  # Optional: Custom build phase
  buildPhase = ''
    npm run build
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp -r dist $out/
    makeWrapper ${nodejs}/bin/node $out/bin/${pname} \
      --add-flags "$out/dist/index.js"
  '';

  meta = { ... };
}
```

### Fetchers

#### fetchFromGitHub
```nix
src = fetchFromGitHub {
  owner = "owner-name";
  repo = "repo-name";
  rev = "v${version}";  # or commit hash
  hash = "sha256-...";  # Use lib.fakeHash initially
  # Optional:
  fetchSubmodules = true;
};
```

#### fetchurl
```nix
src = fetchurl {
  url = "https://example.com/file-${version}.tar.gz";
  hash = "sha256-...";
};
```

#### fetchPypi
```nix
src = fetchPypi {
  inherit pname version;
  hash = "sha256-...";
  # Optional:
  extension = "zip";
};
```

### Hash Management

**Getting correct hashes:**
1. Use `lib.fakeHash` or `lib.fakeSha256` initially
2. Run build, it will fail with actual hash
3. Copy actual hash into derivation
4. Rebuild to verify

```nix
# Initial attempt
hash = lib.fakeHash;

# After failure, copy the hash from error message
hash = "sha256-Abc123...";
```

**For Rust crates:**
```bash
# Prefetch cargo dependencies
nix-prefetch-url --unpack "https://crates.io/api/v1/crates/package/1.0.0/download"
```

## Flakes

### Flake Structure

Standard flake template:
```nix
{
  description = "Package or system description";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = pkgs.callPackage ./default.nix { };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustc
            cargo
            pkg-config
            openssl
          ];
        };

        # For NixOS modules
        nixosModules.default = import ./module.nix;
      });
}
```

### Flake Updates

```bash
# Update all inputs
nix flake update

# Update specific input
nix flake lock --update-input nixpkgs

# Show flake metadata
nix flake metadata

# Check flake for issues
nix flake check
```

## NixOS Configuration

### Module Structure

```nix
{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.myservice;
in
{
  options.services.myservice = {
    enable = mkEnableOption "myservice";

    package = mkOption {
      type = types.package;
      default = pkgs.myservice;
      description = "Package to use for myservice";
    };

    port = mkOption {
      type = types.port;
      default = 8080;
      description = "Port to listen on";
    };

    settings = mkOption {
      type = types.attrs;
      default = { };
      description = "Additional settings";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.myservice = {
      description = "My Service";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/myservice --port ${toString cfg.port}";
        Restart = "always";
        User = "myservice";
        Group = "myservice";
      };
    };

    users.users.myservice = {
      isSystemUser = true;
      group = "myservice";
    };

    users.groups.myservice = { };
  };
}
```

### Common NixOS Patterns

**Service with configuration file:**
```nix
config = mkIf cfg.enable {
  environment.etc."myservice/config.json".text = builtins.toJSON cfg.settings;

  systemd.services.myservice = {
    serviceConfig = {
      ExecStart = "${cfg.package}/bin/myservice --config /etc/myservice/config.json";
    };
  };
};
```

**Conditional package installation:**
```nix
environment.systemPackages = optional cfg.enable cfg.package;
```

## Overlays

### Creating Overlays

```nix
# overlays/default.nix
final: prev: {
  mypackage = prev.mypackage.overrideAttrs (old: {
    version = "2.0.0";
    src = prev.fetchFromGitHub {
      owner = "owner";
      repo = "repo";
      rev = "v2.0.0";
      hash = "sha256-...";
    };
  });

  # Add new package
  newpackage = prev.callPackage ./packages/newpackage.nix { };
}
```

### Using Overlays in Configuration

```nix
# configuration.nix
{ config, pkgs, ... }:

{
  nixpkgs.overlays = [
    (import ./overlays/default.nix)
  ];
}
```

## Troubleshooting Build Failures

### Common Issues

**Missing dependencies:**
```bash
# Check what's in the build environment
nix-build --keep-failed
cd /tmp/nix-build-*
# Inspect what's available
```

**Hash mismatches:**
- Upstream changed release without version bump
- Fetch different source (git tag vs release tarball)
- Use `lib.fakeHash` and copy correct hash from error

**Cross-compilation issues:**
- Check `nativeBuildInputs` vs `buildInputs`
- Some tools must be native (run during build)
- Libraries should be in `buildInputs` (linked into output)

**Cargo/NPM dependency issues:**
- Update `cargoHash` / `npmDepsHash`
- Check for git dependencies in Cargo.toml
- May need `outputHashes` for git dependencies

**Test failures:**
- Set `doCheck = false` if tests require network/special setup
- Use `checkPhase` to customize test execution
- Add to `checkInputs` if test dependencies missing

### Debug Commands

```bash
# Show derivation details
nix show-derivation .#package

# Build with verbose output
nix build -L .#package

# Enter build environment
nix develop .#package

# Check what's in closure
nix path-info -r .#package

# Show why package is in closure
nix why-depends .#system .#package
```

## Nixpkgs Contribution

### Testing Changes

```bash
# Test build
nix-build -A package

# Test NixOS module
nixos-rebuild build --flake .#hostname

# Run package
nix run .#package

# Check for evaluation errors
nix-instantiate --eval '<nixpkgs>' -A package.meta
```

### Pre-commit Checks

```bash
# Format Nix files
nixfmt **/*.nix
# or
alejandra **/*.nix

# Check evaluation
nix flake check

# Run nixpkgs-review (for nixpkgs PRs)
nixpkgs-review pr <PR-number>
```

### Metadata Requirements

All packages MUST include:
```nix
meta = with lib; {
  description = "Brief description (no package name)";
  homepage = "https://...";
  license = licenses.mit;  # or appropriate license
  maintainers = with maintainers; [ your-handle ];
  # For executables:
  mainProgram = "executable-name";
  # Platform support:
  platforms = platforms.unix;  # or platforms.linux, platforms.all
  # If package is known broken:
  broken = false;
};
```

## Common Patterns

### makeWrapper for Scripts

```nix
{ lib, stdenv, makeWrapper, python3, ... }:

stdenv.mkDerivation {
  # ...
  nativeBuildInputs = [ makeWrapper ];
  
  installPhase = ''
    mkdir -p $out/bin
    cp script.py $out/bin/script
    
    wrapProgram $out/bin/script \
      --prefix PATH : ${lib.makeBinPath [ python3 ]}
  '';
}
```

### Patches

```nix
{
  patches = [
    ./patches/fix-build.patch
    (fetchpatch {
      url = "https://github.com/owner/repo/commit/abc123.patch";
      hash = "sha256-...";
    })
  ];
}
```

### postPatch for File Modifications

```nix
{
  postPatch = ''
    # Fix hardcoded paths
    substituteInPlace src/main.rs \
      --replace '/usr/bin/env' '${coreutils}/bin/env'
    
    # Update version in file
    sed -i 's/version = "0.0.0"/version = "${version}"/' Cargo.toml
  '';
}
```

### Conditional Dependencies

```nix
buildInputs = [ 
  common-dep
] ++ lib.optionals stdenv.isDarwin [
  darwin.apple_sdk.frameworks.Security
] ++ lib.optionals stdenv.isLinux [
  systemd
];
```

## File Organization

### Package File Structure
```
package-name/
├── default.nix          # Main derivation
├── cargo.lock          # If using cargoLock
└── patches/            # Patches directory
    └── fix-thing.patch
```

### Multi-Package Repository
```
repo/
├── flake.nix
├── flake.lock
├── packages/
│   ├── package1/
│   │   └── default.nix
│   └── package2/
│       └── default.nix
├── modules/
│   └── service.nix
└── overlays/
    └── default.nix
```

## Quick Reference

**Essential commands:**
- Build: `nix-build -A <attr>` or `nix build .#<package>`
- Develop: `nix develop` or `nix-shell`
- Run: `nix run .#<package>`
- Search: `nix search nixpkgs <query>`
- Format: `nixfmt *.nix` or `alejandra .`

**Hash helpers:**
- Use `lib.fakeHash` initially
- Cargo: update `cargoHash` when Cargo.lock changes
- NPM: update `npmDepsHash` when package-lock.json changes
- Source: update `hash` when version/source changes

**Key principles:**
- MUST declare all dependencies
- MUST NOT access network in build phase
- MUST use appropriate buildInputs classification
- SHOULD use latest package builder patterns
- SHOULD include comprehensive meta
- MUST test build before submitting to nixpkgs

**Common mistakes:**
- Wrong input classification (native vs build)
- Missing `mainProgram` in meta
- Hardcoded store paths instead of references
- Network access during build
- Missing propagated dependencies
- Outdated hashes after updates

---

**Note:** For project-specific Nix patterns, check `.claude/CLAUDE.md` in the project directory.
