# NoPing for Slack
[![built at | Hack Club](https://img.shields.io/badge/built_at-Hack_Club-%23ec3750?logo=hackclub)](https://hackclub.com)

<b>NoPing</b> is a Slack app that adds the `/np` command, letting you link to a user without mentioning (pinging) them.

## Examples
### `/np`: Send a message without mentioning users
In a help channel, you might want to direct someone to a helper.
In this case, a link would be useful, but you might not want to disturb them.
This is one use case for NoPing:
```
/np You might want to DM @helper, who has admin access on the server.
```
> [`@your name`](): You might want to DM [@helper](), who has admin access on the server.

Notice how `@helper` gets turned into a link. In Slack, links to user profiles don't mention the user.

### Escaping pings
Slack mentions followed by `\` are "escaped" by NoPing and will always be pinged.
To prevent accidental usage, `\` can't be preceded by _anything_ other than the mention (or a single space).

```
/np @PleasePingMe \: Sure!
```
> [`@your name`](): {[`@PleasePingMe`]()}: Sure!

### Deleting a message
NoPing provides a shortcut which lets the sender edit or delete the message.
