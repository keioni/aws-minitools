# aws-minitools
AWSに関するミニツールを作っています。

## Lambda - accounting
AWSの Cost Explorer を使って指定期間の費用を取得し、Slackで通知する Lambda です。よくあるスクリプトのような気もします。

## Lambda - instance-ops
まだ作りかけ（というか習作レベル）のスクリプト。いろいろな条件でEC2インスタンスを制御したい、という野望のもとに作り始めたものの現在休止中。

## securitygroup-manager
Perlで書いたセキュリティグループの操作ツール。AWS CLI を活用するスタイルで、サクッと作ろうと思うとこの方法が一番楽なんですよね……。
