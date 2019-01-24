(require 'font-lock)

(defvar ga-mode-hook nil)

(setq ga-instructions-1 '( "ret" "nop""ex" "jump" "call" "unext" "next" "if"
			   "and" "or" "drop" "dup" "pop" "over" "a" "push" ))

(setq ga-instructions-2 '("@+" "!+" "+*" "2*" "2/" "!p"  "!b" "!" "-if"
                          ";" "." "-" "+"  "@p" "@b" "@" "b!" "a!"))

(setq ga-ports '("up" "left" "down" "right" "io"
                 "north" "east" "south" "west"))

(setq ga-directives '( "start" "for" "begin" "then" "here"
                       "while"  "reclaim" "leap"))

(setq ga-directives2 '(".." "#swap" "-while" "," "-until"
                       "---u" "--l-" "--lu" "-d--" "-d-u"
                       "-dl-" "-dlu" "r---" "r--u" "r-l-"
                       "r-lu" "rd--" "rd-u" "rdl-" "rdlu"))

;;directives that take an argument
(setq ga-directives-3 '("node" "org" "include"))

(setq boot-descriptors '("/b" "/a" "/io" "/p" "/stack"))

(defun ga-make-regexp (strings &optional word)
  (let ((x (concat "\\("
		   (mapconcat 'regexp-quote strings "\\|")
		   "\\)")))
    (if word
	(concat "\\<" x "\\>")
      x)))

(setq ga-number-regexp
      "\\<\\(\\(0x[0-9a-fA-F]+\\)\\|\\(0b[01]+\\)\\|[0-9]+\\)\\>")
(setq ga-instruction-regexp-1 (ga-make-regexp ga-instructions-1 t))
(setq ga-instruction-regexp-2 (ga-make-regexp ga-instructions-2))
(setq ga-directive-regexp (ga-make-regexp ga-directives t))
(setq ga-directive-regexp-2 (ga-make-regexp ga-directives2))
(setq ga-ports-regexp (ga-make-regexp ga-ports t))
(setq ga-boot-descriptor-regex (ga-make-regexp boot-descriptors))
(setq ga-directive-regexp-3
      (concat "\\(" (mapconcat (lambda (x)
                                 (format "%s[ ]+[a-zA-Z0-9_.-]+" x))
                               ga-directives-3
                               "\\|")
              "\\)"))
(ga-make-regexp '("b!"))

(defface ga-instruction-face '((((background light)) (:foreground "green"))
                               (((background dark)) (:foreground "green")))
  "Default face for arrayforth instructions")

(defface ga-directive-face '((((background light)) (:foreground "yellow"))
                             (((background dark)) (:foreground "yellow")))
  "Default face for arrayforth compiler directives")

(defface ga-number-face '((((background light)) (:foreground "LightGreen"))
                          (((background dark)) (:foreground "LightGreen")))
  "Default face for arrayforth numbers")

(defface ga-word-face '((((background light)) (:foreground "red"))
                        (((background dark)) (:foreground "red")))
  "Default face for arrayforth word definitions")

(defface ga-boot-descriptor-face '((((background light))
                                    (:foreground "maroon"))
                                   (((background dark))
                                    (:foreground "maroon")))
  "Default face for arrayforth boot descriptors")

(defface ga-word-reference-face '((((background light))
                                   (:foreground "DeepPink"))
                                  (((background dark))
                                   (:foreground "DeepPink")))
  "Default face for arrayforth boot descriptors")

(setq ga-instruction-face 'ga-instruction-face)
(setq ga-directive-face 'ga-directive-face)
(setq ga-word-face 'ga-word-face)
(setq ga-number-face 'ga-number-face)
(setq ga-boot-descriptor-face 'ga-boot-descriptor-face)
(setq ga-word-reference-face 'ga-word-reference-face)

(setq ga-indent-words '((("if" "begin" "for")    (0 . 2) (0 . 2))
			(("then" "next" "unext") (-2 . 0) (0 . -2))
			(("while" "-while")      (-2 . 4) (0 . 2))))

(setq ga-font-lock-keywords
      `(;;word definitions
        ("\\(::\\)[ \t\n]+\\([a-zA-Z0-9_+!@.*/\-]+\\)"
	 (1 ga-directive-face)
	 (2 ga-directive-face))
	("\\(:\\)[ \t\n]+\\([a-zA-Z0-9_+!@.*/\-]+\\)"
	 (1 ga-word-face)
	 (2 ga-word-face))
        ("&[a-zA-Z0-9]+" . ga-word-reference-face)
	(,ga-boot-descriptor-regex . ga-boot-descriptor-face)
        (,ga-directive-regexp-2 . ga-directive-face)
	(,ga-directive-regexp . ga-directive-face)
        (,ga-directive-regexp-3 . ga-directive-face)
	(,ga-instruction-regexp-2 . ga-instruction-face)
	(,ga-instruction-regexp-1 . ga-instruction-face)
	(,ga-ports-regexp . ga-instruction-face)
        (,ga-number-regexp . ga-number-face)
	))

(defvar ga-mode-syntax-table
  (let ((table (make-syntax-table)))
    (modify-syntax-entry ?\\ "<" table)
    (modify-syntax-entry ?\n ">" table)
    (modify-syntax-entry ?\( "<1" table)
    (modify-syntax-entry ?\) ">4" table)
    (modify-syntax-entry ?\: "(" table)
    (modify-syntax-entry ?\; ")" table)
    table)
  "Syntax table in use in ga buffers")

;; imenu support

(defvar ga-defining-words
  '(":")
  "List of words, that define the following word.
Used for imenu index generation.")

(defvar ga-defining-words-regexp nil
  "Regexp that's generated for matching `ga-defining-words'")

(defun ga-next-definition-starter ()
  (progn
    (let* ((pos (re-search-forward ga-defining-words-regexp (point-max) t)))
      (if pos
	  (if (or (text-property-not-all (match-beginning 0) (match-end 0)
					 'ga-parsed nil)
		  (text-property-not-all (match-beginning 0) (match-end 0)
					 'ga-state nil)
                  nil)
	      (ga-next-definition-starter)
	    t)
	nil))))

(defun ga-create-index ()
  (let* ((ga-defining-words-regexp
	  ;;(concat "\\<\\(" (regexp-opt ga-defining-words) "\\)\\>")
          (concat "\\(" (regexp-opt ga-defining-words) "\\)")
          )
	 (index nil))
    (goto-char (point-min))
    (while (ga-next-definition-starter)
      (if (looking-at "[ \t]*\\([^ \t\n]+\\)")
	  (setq index (cons (cons (match-string 1) (point)) index))))
    index))

(defun ga-fill-paragraph (&rest args)
  (let ((fill-paragraph-function nil)
	(fill-paragraph-handle-comment t)
	(comment-start "\\ ")
	(comment-end ""))
    (apply #'fill-paragraph args)))

(defun ga-comment-region (&rest args)
  (let ((comment-start "\\ ")
	(comment-end ""))
    (apply #'comment-region-default args)))

(defun ga-beginning-of-defun (arg)
  (and (re-search-backward "^\\s *: \\_<" nil t (or arg 1))
       (beginning-of-line)))

(define-derived-mode ga-mode prog-mode "ga"
  "Major mode for editing ga files"
  (setq font-lock-defaults '((ga-font-lock-keywords)))

  (set-syntax-table ga-mode-syntax-table)
  (setq-local parse-sexp-lookup-properties t)
  (setq-local fill-paragraph-function #'ga-fill-paragraph)
  (setq-local ga-of-defun-function #'ga-beginning-of-defun)
  (setq-local comment-start "( ")
  (setq-local comment-end " )")
  (setq-local comment-start-skip "[(\\][ \t*]+")
  (setq-local comment-region-function #'ga-comment-region)

  (setq imenu-create-index-function 'ga-create-index)
  (run-hooks 'ga-mode-hook)
  )

(add-to-list 'auto-mode-alist '("\\.ga\\'" . ga-mode))

(provide 'ga-mode)
