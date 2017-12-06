# gitNaughty
A tool for assessing the prevalence of improperly exposed keys in GitHub public repositories

## Network Security Final Project
Our team decided to scan GitHub for API tokens and RSA private keys people had accidentally committed to public repos. The purpose of the project was to determine how widespread this issue has become.

## Results
An actual match found while searching:

```
-----BEGIN RSA PRIVATE KEY-----
  lol. you didn't really think that
  we'd put the key here, in a test,
  did you?!
-----END RSA PRIVATE KEY-----
```

The above match didn't make this mistake but we found thousands and thousands of API tokens and RSA keys in public repos!

## Removing Sensitive Files
If you have accidentally committed a file with sensitive data, follow the steps below to remove it.

- https://help.github.com/articles/removing-sensitive-data-from-a-repository/
- https://stackoverflow.com/questions/307828/completely-remove-file-from-all-git-repository-commit-history
