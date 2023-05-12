# How to setup for development

```
bash setup_devenv.sh
```

# How to upgrade the devenv

```
bash kill_devenv.sh
bash setup_devenv.sh
```

# How to recreate the devenv if something is broken in your db

```
bash kill_devenv.sh
```

Next, delete all directories under dev-files. BUT DO NOT DELETE the .gitignore.

```
bash setup_devenv.sh
```